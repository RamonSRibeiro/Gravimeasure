import io
import base64
import logging
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.interpolate import griddata, RBFInterpolator
from scipy.spatial import ConvexHull
from matplotlib.path import Path

# Configuração para backend não interativo (essencial para Django/Threads)
matplotlib.use('Agg')

from ..models import MedicaoGravimetrica

logger = logging.getLogger(__name__)

def gerar_mapa_contorno_medicao(medicao_foco):
    """
    Gera um mapa de contorno baseado na anomalia de Bouguer
    utilizando interpolação RBF e máscara de Convex Hull.
    """
    # Filtro de dados brutos
    qs = MedicaoGravimetrica.objects.filter(
        ativo=True,
        anomalia_bouguer__gte=-500,
        anomalia_bouguer__lte=500
    ).exclude(anomalia_bouguer__isnull=True)
    
    if qs.count() < 4:
        return None

    longs = np.array([float(m.longitude) for m in qs])
    lats = np.array([float(m.latitude) for m in qs])
    vals = np.array([float(m.anomalia_bouguer) for m in qs])

    f_long, f_lat = float(medicao_foco.longitude), float(medicao_foco.latitude)

    # Ajuste de Zoom
    std_long, std_lat = np.std(longs), np.std(lats)
    z_factor = 0.8 
    xlims = (f_long - (std_long * z_factor), f_long + (std_long * z_factor))
    ylims = (f_lat - (std_lat * z_factor), f_lat + (std_lat * z_factor))

    xi = np.linspace(longs.min() - 0.1, longs.max() + 0.1, 300)
    yi = np.linspace(lats.min() - 0.1, lats.max() + 0.1, 300)
    X, Y = np.meshgrid(xi, yi)

    try:
        obs_coords = np.column_stack((longs, lats))
        grid_coords = np.column_stack((X.ravel(), Y.ravel()))
        
        interpolador = RBFInterpolator(
            obs_coords, 
            vals, 
            kernel='thin_plate_spline', 
            smoothing=0.1
        )
        Z_flat = interpolador(grid_coords)
        Z = Z_flat.reshape(X.shape)
        
    except Exception as e:
        logger.error(f"Erro na interpolação RBF: {e}")
        # Fallback de segurança: Linear
        Z = griddata((longs, lats), vals, (X, Y), method='linear')

    # MÁSCARA CONVEX HULL
    pts = np.column_stack((longs, lats))
    hull = ConvexHull(pts)
    hull_path = Path(pts[hull.vertices])
    mask = hull_path.contains_points(np.column_stack((X.flatten(), Y.flatten()))).reshape(X.shape)
    Z[~mask] = np.nan

    # Normalização de cores focada na área visível
    v_mask = (X >= xlims[0]) & (X <= xlims[1]) & (Y >= ylims[0]) & (Y <= ylims[1]) & (~np.isnan(Z))
    z_vis = Z[v_mask]
    
    if z_vis.size > 0 and not np.all(np.isnan(z_vis)):
        z_min = np.nanpercentile(z_vis, 2)
        z_max = np.nanpercentile(z_vis, 98)
        
        if z_min == z_max:
            levels = 50
            isoline_levels = 10
        else:
            levels = np.linspace(z_min, z_max, 50)
            isoline_levels = np.linspace(z_min, z_max, 12) 
    else:
        levels = 50
        isoline_levels = 10

    fig, ax = plt.subplots(figsize=(8, 7), dpi=200)
    
    if isinstance(levels, np.ndarray):
        # Fundo colorido
        cntr = ax.contourf(X, Y, Z, levels=levels, cmap="turbo", extend='both', vmin=z_min, vmax=z_max)
        fig.colorbar(cntr, ax=ax, label='Anomalia Observada (mGal)')
        
        # Isolinhas
        lines = ax.contour(X, Y, Z, levels=isoline_levels, colors='black', linewidths=0.5, alpha=0.6, vmin=z_min, vmax=z_max)
        ax.clabel(lines, inline=True, fontsize=7, fmt='%.1f')

    # Marcadores
    ax.scatter(longs, lats, c='black', s=10, alpha=0.3, zorder=3)
    ax.scatter(f_long, f_lat, c='gold', s=350, marker='*', edgecolors='black', linewidths=1.2, zorder=10)

    ax.set_xlim(xlims)
    ax.set_ylim(ylims)
    ax.set_aspect('equal')
    
    ax.set_xlabel('Longitude (°W)')
    ax.set_ylabel('Latitude (°S)')
    
    codigo = getattr(medicao_foco, 'codigo_estacao', 'Desconhecida')
    ax.set_title(f"Mapa Bouguer: Estação {codigo}", pad=20)
    ax.grid(True, linestyle='--', alpha=0.1)

    # Conversão para Base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"