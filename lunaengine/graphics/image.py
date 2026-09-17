"""Common surface-backed image abstraction used by graphics and UI."""
from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple, Union
import pygame

ImageSource = Union[pygame.Surface, "Image", str, Path]

class Image:
    """Lazy, cacheable pygame image. Explicit pixel size takes precedence over scale."""
    def __init__(self, source: ImageSource, source_rect=None, *, scale=1.0,
                 size: Optional[Tuple[int, int]] = None, alpha=1.0,
                 filters=None, mask: Optional[ImageSource] = None):
        if isinstance(source, Image): source = source.get_surface()
        elif isinstance(source, (str, Path)): source = pygame.image.load(str(source)).convert_alpha()
        if not isinstance(source, pygame.Surface): raise TypeError("source must be a pygame.Surface, Image, or image path")
        self._source = source
        self._source_rect = pygame.Rect(source_rect) if source_rect is not None else None
        self._scale = scale
        self._size = tuple(size) if size is not None else None
        self._alpha = max(0.0, min(1.0, float(alpha)))
        self._filters = list(filters or [])
        self._mask = mask
        self._revision = 0
        self._cache = {}

    @property
    def source(self): return self._source
    @property
    def scale(self): return self._scale
    @property
    def size(self): return self._size
    @property
    def alpha(self): return self._alpha
    def _dirty(self): self._revision += 1; self._cache.clear(); return self
    def set_scale(self, scale):
        self._scale = (float(scale[0]), float(scale[1])) if isinstance(scale, (tuple,list)) else float(scale); return self._dirty()
    def set_size(self, size): self._size = tuple(map(int,size)) if size is not None else None; return self._dirty()
    def set_alpha(self, alpha): self._alpha = max(0.0,min(1.0,float(alpha))); return self._dirty()
    def set_source_rect(self, rect): self._source_rect = pygame.Rect(rect) if rect is not None else None; return self._dirty()
    def set_filter(self, name, **params): self._filters.append((str(name).lower(),dict(params))); return self._dirty()
    def clear_filters(self): self._filters.clear(); return self._dirty()
    def set_mask(self, mask): self._mask = mask; return self._dirty()

    def get_surface(self):
        key=(self._revision,self._scale,self._size,self._alpha,tuple((n,tuple(sorted(p.items()))) for n,p in self._filters),id(self._mask),getattr(self._mask,'_revision',0))
        if key in self._cache: return self._cache[key]
        result=self._source.copy()
        if self._source_rect is not None: result=result.subsurface(self._source_rect).copy()
        for name,params in self._filters: result=self._apply_filter(result,name,params)
        if self._mask is not None:
            mask=self._mask.get_surface() if hasattr(self._mask,'get_surface') else self._mask
            if mask.get_size()!=result.get_size(): mask=pygame.transform.smoothscale(mask,result.get_size())
            out=result.copy()
            for y in range(result.get_height()):
                for x in range(result.get_width()):
                    p= result.get_at((x,y)); m=mask.get_at((x,y)); out.set_at((x,y),(p[0],p[1],p[2],(p[3]*m[3])//255))
            result=out
        if self._size is not None: result=pygame.transform.smoothscale(result,self._size)
        elif self._scale != 1.0:
            sx,sy=self._scale if isinstance(self._scale,(tuple,list)) else (self._scale,self._scale)
            result=pygame.transform.smoothscale(result,(max(1,round(result.get_width()*sx)),max(1,round(result.get_height()*sy))))
        if self._alpha < 1.0: result=result.copy(); result.set_alpha(round(self._alpha*255))
        self._cache[key]=result; return result

    def _apply_filter(self,surface,name,params):
        from .spritesheet import SpriteSheet
        if name=='tint': return SpriteSheet.tint(surface,params.get('color',params.get('tint_color',(255,255,255))),params.get('intensity',1.0),params.get('blend_mode','multiply'))
        if name in ('replace','replace_color'): return SpriteSheet.replace_color(surface,params['old'],params['new'],params.get('tolerance',0))
        if name in ('paint','silhouette'): return SpriteSheet.paint(surface,params.get('color',(255,255,255)),params.get('preserve_alpha',True))
        out=surface.copy()
        if name=='grayscale':
            for y in range(out.get_height()):
                for x in range(out.get_width()):
                    p=out.get_at((x,y)); g=round(.299*p[0]+.587*p[1]+.114*p[2]); out.set_at((x,y),(g,g,g,p[3]))
            return out
        if name in ('brightness','contrast'):
            factor=float(params.get('amount',params.get('factor',1.0)))
            for y in range(out.get_height()):
                for x in range(out.get_width()):
                    p=out.get_at((x,y)); vals=[max(0,min(255,round((c-128)*factor+128))) for c in p[:3]] if name=='contrast' else [max(0,min(255,round(c*factor))) for c in p[:3]]; out.set_at((x,y),(*vals,p[3]))
            return out
        raise ValueError(f'Unsupported image filter: {name}')
    def copy(self): return Image(self._source.copy(),self._source_rect,scale=self._scale,size=self._size,alpha=self._alpha,filters=self._filters,mask=self._mask)
    def __getattr__(self,name): return getattr(self.get_surface(),name)
    def __repr__(self): return f'Image(size={self.get_surface().get_size()}, scale={self._scale}, alpha={self._alpha})'
