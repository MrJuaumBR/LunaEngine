"""
lunaengine/storage/savedata.py

A powerful, table‑based save‑data system for LunaEngine.
- Multiple tables with typed columns
- Insert, update, delete, select with filtering
- Primary key indexing for fast lookups
- Auto‑increment for integer primary keys
- Upsert (insert or update)
- Bulk update by primary key via `updates()` dict
- Advanced query support: ordering, searching (contains, startswith, endswith, exact, case‑sensitive)
- Custom binary file format with compression (zlib) and optional encryption
- Export/Import to JSON for machine migration
- Integrates with MachineEncryption for HWID‑based XOR encryption

Usage:
    data = Savedata("game.sav")
    users = data.create_table("users", ["id", "name", "score"],
                              primary_key="id", auto_increment=True)
    users.insert(name="Alice", score=100)       # id auto‑assigned
    users.insert(id=5, name="Bob", score=200)   # manual ID
    data.save()

    # Update by primary key
    users.update_by_primary_key(1, score=150)

    # Upsert
    users.upsert(id=2, name="Charlie", score=300)

    # Bulk update by primary keys
    users.updates({
        1: {"name": "Alicia", "score": 110},
        5: {"score": 250}
    })

    # Advanced select with query builder
    results = users.query() \\
        .where(lambda r: r["score"] > 50) \\
        .order_by("score", desc=True) \\
        .search("al", columns=["name"], mode="contains") \\
        .execute()

    # Export to JSON for migration
    data.export_to_json("backup.json")
    # On another machine:
    data.import_from_json("backup.json")
"""

import os
import json
import zlib
import struct
import pickle
import functools
import operator
from typing import Dict, List, Any, Optional, Union, Callable, Tuple, Iterable
from pathlib import Path
try:
    from .encrypter import MachineEncryption
except ImportError:
    MachineEncryption = None


class SavedataError(Exception):
    """Base exception for Savedata errors."""
    pass


class Table:
    """
    A table in the savedata: stores rows as dictionaries with column names as keys.
    Supports primary key indexing for O(1) lookups and optional auto‑increment.
    """

    def __init__(self, name: str, columns: List[str],
                 primary_key: Optional[str] = None,
                 auto_increment: bool = False):
        """
        Args:
            name: Table name.
            columns: Ordered list of column names.
            primary_key: Column name to use as primary key (must be in columns).
            auto_increment: If True and primary_key is an integer column, automatically
                            assign the next ID on insert when the key is omitted.
        """
        self.name = name
        self.columns = columns[:]
        self.primary_key = primary_key
        if primary_key and primary_key not in columns:
            raise ValueError(f"Primary key '{primary_key}' not in columns")
        self.rows: List[Dict[str, Any]] = []
        self._index: Dict[Any, int] = {}  # primary_key_value -> row index
        self.auto_increment = auto_increment
        self._next_id = 1  # only used if auto_increment and primary_key is int
        if auto_increment and primary_key:
            self._update_next_id()  # compute from existing rows (if any)

    def insert(self, **kwargs) -> int:
        """
        Insert a row. Keyword arguments must match the table's columns.
        If auto_increment is enabled and the primary key is not provided,
        the next ID is assigned automatically.
        Returns the row index.
        """
        row = {col: kwargs.get(col, None) for col in self.columns}
        for key in kwargs:
            if key not in self.columns:
                raise ValueError(f"Unknown column '{key}' for table '{self.name}'")

        # Auto‑increment handling
        if self.auto_increment and self.primary_key:
            pk_val = row.get(self.primary_key)
            if pk_val is None:
                # Assign next ID
                pk_val = self._next_id
                row[self.primary_key] = pk_val
                self._next_id += 1
            else:
                # Ensure the provided ID is at least the current next_id
                if isinstance(pk_val, int) and pk_val >= self._next_id:
                    self._next_id = pk_val + 1
                # If it's not an int, auto‑increment doesn't apply (we don't update next_id)

        self.rows.append(row)
        idx = len(self.rows) - 1
        if self.primary_key:
            key_val = row[self.primary_key]
            if key_val is None:
                raise ValueError(f"Primary key '{self.primary_key}' cannot be None")
            if key_val in self._index:
                raise ValueError(f"Duplicate primary key value '{key_val}'")
            self._index[key_val] = idx
        return idx

    def update(self, where: Callable[[Dict], bool], **kwargs) -> int:
        """
        Update rows that match the where predicate with the given kwargs.
        Returns the number of updated rows.
        """
        return self.update_where(where, kwargs)

    def update_where(self, where: Callable[[Dict], bool],
                     updates: Dict[str, Any]) -> int:
        """
        Update rows that match the where predicate with the given updates dict.
        Returns the number of updated rows.
        """
        count = 0
        for idx, row in enumerate(self.rows):
            if where(row):
                for col, val in updates.items():
                    if col not in self.columns:
                        raise ValueError(f"Unknown column '{col}'")
                    row[col] = val
                count += 1
                if self.primary_key and self.primary_key in updates:
                    new_key = row[self.primary_key]
                    old_key = self._find_primary_key_for_idx(idx)
                    if old_key != new_key:
                        del self._index[old_key]
                        self._index[new_key] = idx
                        # Update next_id if auto_increment and new_key is int
                        if self.auto_increment and isinstance(new_key, int):
                            if new_key >= self._next_id:
                                self._next_id = new_key + 1
        return count

    def update_by_primary_key(self, key: Any, **kwargs) -> int:
        """
        Update the row with the given primary key using the provided kwargs.
        Returns 1 if updated, 0 if not found.
        """
        if not self.primary_key:
            raise ValueError("Table has no primary key")
        idx = self._index.get(key)
        if idx is None:
            return 0
        # Use update_where on a predicate that matches this row
        return self.update_where(lambda r: r[self.primary_key] == key, kwargs)

    def updates(self, updates_dict: Dict[Any, Union[Any, Dict[str, Any]]]) -> int:
        """
        Update multiple rows by primary key.

        Args:
            updates_dict: A dictionary where keys are primary key values,
                          and values are either:
                            - a dict mapping column names to new values
                            - a scalar value (shorthand):
                                - If the table has exactly one non‑primary‑key column,
                                  that column is updated with this value.
                                - Otherwise, if a column named 'value' exists,
                                  that column is updated.
                                - Else, raises ValueError.

        Returns:
            The number of rows that were updated (i.e., keys that existed).
        """
        if not self.primary_key:
            raise ValueError("Table has no primary key")

        # Determine the target column for scalar shorthand
        non_pk_columns = [c for c in self.columns if c != self.primary_key]
        scalar_column = None
        if len(non_pk_columns) == 1:
            scalar_column = non_pk_columns[0]
        elif 'value' in self.columns:
            scalar_column = 'value'
        # else: scalar not allowed

        count = 0
        for pk_val, update in updates_dict.items():
            idx = self._index.get(pk_val)
            if idx is None:
                continue  # skip missing keys (or we could raise, but we choose to skip)
            # Prepare updates dict
            if isinstance(update, dict):
                updates = update
            else:
                # Scalar value
                if scalar_column is None:
                    raise ValueError(
                        f"Cannot use scalar value for key '{pk_val}' because table has multiple non‑PK columns "
                        f"and no 'value' column. Provide a dict mapping columns to values."
                    )
                updates = {scalar_column: update}
            # Apply updates to this row
            row = self.rows[idx]
            for col, val in updates.items():
                if col not in self.columns:
                    raise ValueError(f"Unknown column '{col}'")
                row[col] = val
            # Update primary key index if primary key changed
            if self.primary_key in updates:
                new_key = row[self.primary_key]
                old_key = pk_val  # original key
                if old_key != new_key:
                    del self._index[old_key]
                    self._index[new_key] = idx
                    if self.auto_increment and isinstance(new_key, int):
                        if new_key >= self._next_id:
                            self._next_id = new_key + 1
            count += 1
        return count

    def upsert(self, **kwargs) -> int:
        """
        Insert a new row, or update the existing one if the primary key already exists.
        Returns the row index (for insert) or 1 (for update).
        Raises ValueError if primary key is missing when auto_increment is off.
        """
        if not self.primary_key:
            raise ValueError("Table has no primary key, upsert not supported")
        pk_val = kwargs.get(self.primary_key)
        if pk_val is None:
            if self.auto_increment:
                # Insert with auto‑assigned ID
                return self.insert(**kwargs)
            else:
                raise ValueError(f"Primary key '{self.primary_key}' must be provided for upsert")
        idx = self._index.get(pk_val)
        if idx is not None:
            # Update existing row
            # Remove primary key from updates to avoid changing it (or allow it)
            updates = {k: v for k, v in kwargs.items() if k != self.primary_key}
            if updates:
                self.update_where(lambda r: r[self.primary_key] == pk_val, updates)
            return 1  # updated
        else:
            # Insert new row
            return self.insert(**kwargs)

    def delete(self, where: Callable[[Dict], bool]) -> int:
        """
        Delete rows matching the predicate.
        Returns the number of deleted rows.
        """
        to_delete = [i for i, row in enumerate(self.rows) if where(row)]
        for i in sorted(to_delete, reverse=True):
            if self.primary_key:
                key_val = self.rows[i][self.primary_key]
                self._index.pop(key_val, None)
            self.rows.pop(i)
        if to_delete and self.primary_key:
            self._rebuild_index()
        if self.auto_increment and self.primary_key:
            self._update_next_id()
        return len(to_delete)

    def delete_by_primary_key(self, key: Any) -> int:
        """
        Delete the row with the given primary key.
        Returns 1 if deleted, 0 if not found.
        """
        if not self.primary_key:
            raise ValueError("Table has no primary key")
        return self.delete(lambda r: r[self.primary_key] == key)

    def select(self,
               where: Optional[Callable[[Dict], bool]] = None,
               columns: Optional[List[str]] = None,
               order_by: Optional[Union[str, List[str]]] = None,
               order_desc: Union[bool, List[bool]] = False,
               search: Optional[str] = None,
               search_columns: Optional[List[str]] = None,
               search_mode: str = 'contains',
               case_sensitive: bool = False) -> List[Dict]:
        """
        Select rows with optional filtering, ordering, and searching.

        Args:
            where: Predicate function that takes a row dict and returns True to include.
            columns: List of column names to return. If None, returns all columns.
            order_by: Column name(s) to sort by. Can be a string or list of strings.
            order_desc: If True, sort descending. If a list, must match length of order_by.
            search: Search term to filter rows.
            search_columns: Columns to search in. If None, searches all columns.
            search_mode: 'contains', 'startswith', 'endswith', or 'exact'.
            case_sensitive: If False, performs case‑insensitive search.

        Returns:
            List of row dictionaries (or partial dicts if columns specified).
        """
        filtered = self.rows
        if where is not None:
            filtered = [row for row in self.rows if where(row)]

        if search is not None:
            filtered = self._apply_search(filtered, search, search_columns,
                                          search_mode, case_sensitive)

        if order_by:
            filtered = self._sort_rows(filtered, order_by, order_desc)

        if columns is not None:
            for col in columns:
                if col not in self.columns:
                    raise ValueError(f"Column '{col}' not in table")
            return [{col: row[col] for col in columns} for row in filtered]
        else:
            return [row.copy() for row in filtered]

    def find_one(self, where: Optional[Callable[[Dict], bool]] = None) -> Optional[Dict]:
        """
        Return the first row that matches the predicate, or None if not found.
        """
        if where is None:
            return self.rows[0].copy() if self.rows else None
        for row in self.rows:
            if where(row):
                return row.copy()
        return None

    def exists(self, where: Callable[[Dict], bool]) -> bool:
        """Return True if any row matches the predicate."""
        return any(where(row) for row in self.rows)

    def count(self, where: Optional[Callable[[Dict], bool]] = None) -> int:
        """Return the number of rows (optionally filtered by predicate)."""
        if where is None:
            return len(self.rows)
        return sum(1 for row in self.rows if where(row))

    def get_next_id(self) -> int:
        """
        Return the next auto‑increment ID (only valid if auto_increment is True
        and the primary key is an integer column).
        """
        if not self.auto_increment:
            raise ValueError("Auto‑increment is not enabled for this table")
        if self.primary_key is None:
            raise ValueError("Table has no primary key")
        return self._next_id

    def _apply_search(self, rows: List[Dict], term: str,
                      search_columns: Optional[List[str]],
                      mode: str, case_sensitive: bool) -> List[Dict]:
        """Filter rows based on search term."""
        if not term:
            return rows

        if search_columns is None:
            search_cols = self.columns
        else:
            search_cols = [c for c in search_columns if c in self.columns]
            if not search_cols:
                raise ValueError("No valid search columns specified")

        term_str = term if case_sensitive else term.lower()
        mode = mode.lower()

        def matches(row: Dict) -> bool:
            for col in search_cols:
                val = row.get(col)
                if val is None:
                    continue
                val_str = str(val)
                if not case_sensitive:
                    val_str = val_str.lower()

                if mode == 'contains':
                    if term_str in val_str:
                        return True
                elif mode == 'startswith':
                    if val_str.startswith(term_str):
                        return True
                elif mode == 'endswith':
                    if val_str.endswith(term_str):
                        return True
                elif mode == 'exact':
                    if val_str == term_str:
                        return True
                else:
                    raise ValueError(f"Unknown search_mode: {mode}")
            return False

        return [row for row in rows if matches(row)]

    def _sort_rows(self, rows: List[Dict],
                   order_by: Union[str, List[str]],
                   order_desc: Union[bool, List[bool]]) -> List[Dict]:
        """Sort rows by one or more columns with specified directions."""
        if isinstance(order_by, str):
            order_by = [order_by]
        if isinstance(order_desc, bool):
            order_desc = [order_desc] * len(order_by)
        elif len(order_desc) != len(order_by):
            raise ValueError("order_desc length must match order_by length")

        def cmp(a: Dict, b: Dict) -> int:
            for col, desc in zip(order_by, order_desc):
                va = a.get(col)
                vb = b.get(col)
                if va is None and vb is None:
                    continue
                if va is None:
                    return 1 if not desc else -1
                if vb is None:
                    return -1 if not desc else 1
                try:
                    if va < vb:
                        return 1 if desc else -1
                    elif va > vb:
                        return -1 if desc else 1
                except TypeError:
                    va_str = str(va)
                    vb_str = str(vb)
                    if va_str < vb_str:
                        return 1 if desc else -1
                    elif va_str > vb_str:
                        return -1 if desc else 1
            return 0

        return sorted(rows, key=functools.cmp_to_key(cmp))

    def get_by_primary_key(self, key: Any) -> Optional[Dict]:
        """Retrieve a row by its primary key value, or None if not found."""
        if not self.primary_key:
            raise ValueError("Table has no primary key")
        idx = self._index.get(key)
        if idx is None:
            return None
        return self.rows[idx].copy()

    def clear(self) -> None:
        """Remove all rows."""
        self.rows.clear()
        self._index.clear()
        if self.auto_increment and self.primary_key:
            self._next_id = 1

    def query(self) -> 'Query':
        """
        Return a new Query builder for this table.
        Example:
            rows = table.query() \\
                .where(lambda r: r["score"] > 100) \\
                .order_by("score", desc=True) \\
                .search("al", columns=["name"], mode="contains") \\
                .execute()
        """
        return Query(self)

    def _find_primary_key_for_idx(self, idx: int) -> Any:
        return self.rows[idx][self.primary_key]

    def _rebuild_index(self) -> None:
        self._index.clear()
        for idx, row in enumerate(self.rows):
            key_val = row[self.primary_key]
            if key_val is None:
                raise ValueError(f"Primary key '{self.primary_key}' is None in row {idx}")
            if key_val in self._index:
                raise ValueError(f"Duplicate primary key '{key_val}' found during rebuild")
            self._index[key_val] = idx

    def _update_next_id(self) -> None:
        """Recalculate the next auto‑increment ID from existing rows."""
        if not self.auto_increment or not self.primary_key:
            return
        max_id = 0
        for row in self.rows:
            val = row.get(self.primary_key)
            if isinstance(val, int) and val > max_id:
                max_id = val
        self._next_id = max_id + 1

    def __len__(self) -> int:
        return len(self.rows)

    def __repr__(self) -> str:
        return f"<Table '{self.name}' columns={self.columns} rows={len(self.rows)} auto_increment={self.auto_increment}>"


class Query:
    """Fluent query builder for Table."""

    def __init__(self, table: Table):
        self.table = table
        self._where = None
        self._order_by = None
        self._order_desc = []
        self._search = None
        self._search_columns = None
        self._search_mode = 'contains'
        self._case_sensitive = False

    def where(self, predicate: Callable[[Dict], bool]) -> 'Query':
        self._where = predicate
        return self

    def order_by(self, *columns: str, desc: Union[bool, List[bool]] = False) -> 'Query':
        self._order_by = list(columns)
        if isinstance(desc, list):
            if len(desc) != len(columns):
                raise ValueError("desc list length must match columns count")
            self._order_desc = desc
        else:
            self._order_desc = [desc] * len(columns)
        return self

    def search(self, term: str,
               columns: Optional[List[str]] = None,
               mode: str = 'contains',
               case_sensitive: bool = False) -> 'Query':
        self._search = term
        self._search_columns = columns
        self._search_mode = mode
        self._case_sensitive = case_sensitive
        return self

    def execute(self, columns: Optional[List[str]] = None) -> List[Dict]:
        return self.table.select(
            where=self._where,
            columns=columns,
            order_by=self._order_by,
            order_desc=self._order_desc,
            search=self._search,
            search_columns=self._search_columns,
            search_mode=self._search_mode,
            case_sensitive=self._case_sensitive
        )


class Savedata:
    """
    Main savedata manager. Holds multiple tables and provides load/save functionality.
    Supports compression (zlib) and optional encryption via MachineEncryption.
    File format:
        - Magic bytes: "LUNASD" (7 bytes)
        - Version: uint16
        - Flags: uint8 (bit 0: compressed, bit 1: encrypted)
        - Table count: uint32
        - For each table:
            - Name length (uint16) + name string (UTF-8)
            - Column count (uint16)
            - For each column: name length (uint16) + name string
            - Primary key index (int16, -1 if none)
            - Auto‑increment flag (uint8)
            - Row count (uint32)
            - For each row:
                - For each column:
                    - Type tag (uint8): 0=None, 1=int, 2=float, 3=str, 4=bool, 5=bytes
                    - Data (variable)
    """

    MAGIC = b"LUNASD"
    VERSION = 2  # bumped version due to format change (added auto_increment flag)

    def __init__(self, filepath: Optional[Union[str, Path]] = None,
                 encryption_key: Optional[str] = None):
        """
        Args:
            filepath: Path to the savedata file. If provided and exists, loads automatically.
            encryption_key: Key for XOR encryption (if None, uses default MachineEncryption HWID).
        """
        self.tables: Dict[str, Table] = {}
        self.filepath = Path(filepath) if filepath else None
        self.encryption_key = encryption_key
        if self.filepath and self.filepath.exists():
            self.load(self.filepath, encryption_key)

    def create_table(self, name: str, columns: List[str],
                     primary_key: Optional[str] = None,
                     auto_increment: bool = False) -> Table:
        if name in self.tables:
            raise ValueError(f"Table '{name}' already exists")
        table = Table(name, columns, primary_key, auto_increment)
        self.tables[name] = table
        return table

    def drop_table(self, name: str) -> None:
        if name in self.tables:
            del self.tables[name]

    def table(self, name: str) -> Optional[Table]:
        return self.tables.get(name)

    def clear(self) -> None:
        self.tables.clear()

    def save(self, filepath: Optional[Union[str, Path]] = None,
             encryption_key: Optional[str] = None,
             compress: bool = True) -> None:
        if filepath:
            self.filepath = Path(filepath)
        if not self.filepath:
            raise SavedataError("No filepath specified for save")
        if encryption_key is not None:
            self.encryption_key = encryption_key

        data = self._serialize()
        flags = 0
        if compress:
            data = zlib.compress(data)
            flags |= 0x01
        if self.encryption_key:
            data = self._xor_encrypt(data, self.encryption_key)
            flags |= 0x02

        with open(self.filepath, 'wb') as f:
            f.write(self.MAGIC)
            f.write(struct.pack('<H', self.VERSION))
            f.write(struct.pack('<B', flags))
            f.write(data)

    def load(self, filepath: Optional[Union[str, Path]] = None,
             encryption_key: Optional[str] = None) -> None:
        if filepath:
            self.filepath = Path(filepath)
        if not self.filepath or not self.filepath.exists():
            raise FileNotFoundError(f"Savedata file not found: {self.filepath}")
        if encryption_key is not None:
            self.encryption_key = encryption_key

        with open(self.filepath, 'rb') as f:
            magic = f.read(len(self.MAGIC))
            if magic != self.MAGIC:
                raise SavedataError("Invalid file format (magic mismatch)")
            version = struct.unpack('<H', f.read(2))[0]
            if version != self.VERSION:
                raise SavedataError(f"Unsupported version {version}")
            flags = struct.unpack('<B', f.read(1))[0]
            data = f.read()

        if flags & 0x02:
            if not self.encryption_key:
                raise SavedataError("File is encrypted but no key provided")
            data = self._xor_encrypt(data, self.encryption_key)

        if flags & 0x01:
            data = zlib.decompress(data)

        self._deserialize(data)

    def _serialize(self) -> bytes:
        parts = []
        parts.append(struct.pack('<I', len(self.tables)))
        for name, table in self.tables.items():
            name_bytes = name.encode('utf-8')
            parts.append(struct.pack('<H', len(name_bytes)))
            parts.append(name_bytes)
            parts.append(struct.pack('<H', len(table.columns)))
            for col in table.columns:
                col_bytes = col.encode('utf-8')
                parts.append(struct.pack('<H', len(col_bytes)))
                parts.append(col_bytes)
            pk_idx = table.columns.index(table.primary_key) if table.primary_key else -1
            parts.append(struct.pack('<h', pk_idx))
            parts.append(struct.pack('<?', table.auto_increment))  # auto_increment flag
            parts.append(struct.pack('<I', len(table.rows)))
            for row in table.rows:
                for col in table.columns:
                    value = row.get(col)
                    self._append_value(parts, value)
        return b''.join(parts)

    def _deserialize(self, data: bytes) -> None:
        self.tables.clear()
        pos = 0
        table_count = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        for _ in range(table_count):
            name_len = struct.unpack_from('<H', data, pos)[0]
            pos += 2
            name = data[pos:pos+name_len].decode('utf-8')
            pos += name_len
            col_count = struct.unpack_from('<H', data, pos)[0]
            pos += 2
            columns = []
            for _ in range(col_count):
                col_len = struct.unpack_from('<H', data, pos)[0]
                pos += 2
                col = data[pos:pos+col_len].decode('utf-8')
                pos += col_len
                columns.append(col)
            pk_idx = struct.unpack_from('<h', data, pos)[0]
            pos += 2
            primary_key = columns[pk_idx] if pk_idx >= 0 else None
            auto_increment = struct.unpack_from('<?', data, pos)[0]
            pos += 1
            table = Table(name, columns, primary_key, auto_increment)
            row_count = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            for _ in range(row_count):
                row = {}
                for col in columns:
                    value, pos = self._read_value(data, pos)
                    row[col] = value
                table.rows.append(row)
            if table.primary_key:
                table._rebuild_index()
            if table.auto_increment:
                table._update_next_id()
            self.tables[name] = table

    def _append_value(self, parts: List[bytes], value: Any) -> None:
        if value is None:
            parts.append(struct.pack('<B', 0))
        elif isinstance(value, bool):
            parts.append(struct.pack('<B', 4))
            parts.append(struct.pack('<?', value))
        elif isinstance(value, int):
            parts.append(struct.pack('<B', 1))
            parts.append(struct.pack('<q', value))
        elif isinstance(value, float):
            parts.append(struct.pack('<B', 2))
            parts.append(struct.pack('<d', value))
        elif isinstance(value, str):
            encoded = value.encode('utf-8')
            parts.append(struct.pack('<B', 3))
            parts.append(struct.pack('<I', len(encoded)))
            parts.append(encoded)
        elif isinstance(value, bytes):
            parts.append(struct.pack('<B', 5))
            parts.append(struct.pack('<I', len(value)))
            parts.append(value)
        else:
            # Fallback: pickle
            parts.append(struct.pack('<B', 6))
            pickled = pickle.dumps(value)
            parts.append(struct.pack('<I', len(pickled)))
            parts.append(pickled)

    def _read_value(self, data: bytes, pos: int) -> Tuple[Any, int]:
        tag = data[pos]
        pos += 1
        if tag == 0:
            return None, pos
        elif tag == 1:
            val = struct.unpack_from('<q', data, pos)[0]
            return val, pos + 8
        elif tag == 2:
            val = struct.unpack_from('<d', data, pos)[0]
            return val, pos + 8
        elif tag == 3:
            length = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            val = data[pos:pos+length].decode('utf-8')
            return val, pos + length
        elif tag == 4:
            val = struct.unpack_from('<?', data, pos)[0]
            return val, pos + 1
        elif tag == 5:
            length = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            val = data[pos:pos+length]
            return val, pos + length
        elif tag == 6:
            length = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            pickled = data[pos:pos+length]
            val = pickle.loads(pickled)
            return val, pos + length
        else:
            raise SavedataError(f"Unknown type tag {tag} at position {pos-1}")

    def _xor_encrypt(self, data: bytes, key: str) -> bytes:
        key_bytes = key.encode('utf-8')
        return bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])

    # -------- Export / Import (for migration) --------
    def export_to_dict(self) -> Dict[str, List[Dict]]:
        """
        Export all tables to a dictionary: {table_name: [row_dict, ...]}.
        Useful for serialization to JSON or migration.
        """
        result = {}
        for name, table in self.tables.items():
            result[name] = [row.copy() for row in table.rows]
        return result

    def import_from_dict(self, data: Dict[str, List[Dict]]) -> None:
        """
        Clear all tables and import data from a dictionary.
        Expects the same structure as export_to_dict.
        Columns and primary keys are recreated from the first row.
        Auto‑increment is disabled on imported tables (you can re‑enable manually).
        """
        self.tables.clear()
        for table_name, rows in data.items():
            if not rows:
                continue
            # Infer columns from the first row
            columns = list(rows[0].keys())
            # Try to find a primary key – we can't know automatically; assume first column
            primary_key = columns[0]  # simple heuristic, can be overridden
            table = self.create_table(table_name, columns, primary_key=primary_key,
                                      auto_increment=False)  # disable auto_increment for import
            for row in rows:
                clean_row = {col: row.get(col, None) for col in columns}
                table.rows.append(clean_row)
            if table.primary_key:
                table._rebuild_index()

    def export_to_json(self, filepath: Union[str, Path], indent: int = 2) -> None:
        """Export all tables to a JSON file (unencrypted, no compression)."""
        data = self.export_to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, default=str)

    def import_from_json(self, filepath: Union[str, Path]) -> None:
        """Import tables from a JSON file (clears existing data)."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.import_from_dict(data)

    # -------- Migration helpers --------
    def migrate_to_plain(self, output_path: Union[str, Path]) -> None:
        """
        Save the current data without encryption and without compression.
        Useful for creating a portable backup.
        """
        old_key = self.encryption_key
        self.encryption_key = None
        self.save(output_path, compress=False, encryption_key=None)
        self.encryption_key = old_key

    def migrate_from_plain(self, input_path: Union[str, Path], new_key: Optional[str] = None) -> None:
        """
        Load a plain (unencrypted) file and re-save it with the current encryption key.
        If new_key is provided, use that key for subsequent saves.
        """
        old_key = self.encryption_key
        self.encryption_key = None
        self.load(input_path, encryption_key=None)
        self.encryption_key = new_key if new_key is not None else old_key

    def __repr__(self) -> str:
        return f"<Savedata tables={list(self.tables.keys())}>"


# Convenience functions
def load_savedata(filepath: Union[str, Path], encryption_key: Optional[str] = None) -> Savedata:
    return Savedata(filepath, encryption_key)


def save_savedata(data: Savedata, filepath: Union[str, Path],
                  encryption_key: Optional[str] = None, compress: bool = True) -> None:
    data.save(filepath, encryption_key, compress)