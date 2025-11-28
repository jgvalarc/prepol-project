import { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap, LayersControl } from 'react-leaflet';
import { Box, CircularProgress, Typography, Alert, Divider } from '@mui/material';
import 'leaflet/dist/leaflet.css';
import "./CrimeMap.css";
import L from 'leaflet';
import HexagonTwoToneIcon from '@mui/icons-material/HexagonTwoTone';

// Fix Leaflet default icon issue in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Component to fit map bounds when data changes
function MapBoundsUpdater({ geojson }) {
  const map = useMap();

  useEffect(() => {
    if (geojson && geojson.features && geojson.features.length > 0) {
      const bounds = L.geoJSON(geojson).getBounds();
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [geojson, map]);

  return null;
}

export default function CrimeMap({ forecastData, loading, error }) {
  const [mapCenter] = useState([-8.05, -34.9]); // Recife, Brazil
  const [mapZoom] = useState(11);
  // Selected crime type filters (Set for fast membership checks)
  const [selectedCrimeTypes, setSelectedCrimeTypes] = useState(new Set(['All']));
  // Legend collapsed state (must be at top before any returns)
  const [legendCollapsed, setLegendCollapsed] = useState(false);

  // Color gradient function (light red -> dark red)
  const getRedGradient = (normalizedValue) => {
    // RGB: (255, 200, 200) -> (139, 0, 0)
    const r = Math.floor(255 - (116 * normalizedValue));
    const g = Math.floor(200 - (200 * normalizedValue));
    const b = Math.floor(200 - (200 * normalizedValue));
    return `rgb(${r}, ${g}, ${b})`;
  };

  // Style function for GeoJSON features (matches notebook)
  const styleFeature = (feature) => {
    if (!feature || !feature.properties) return {};
    const p = feature.properties;
    const probability = Number(
      p.probability ?? p.crime_probability ?? p.normalized_prob ?? 0
    );
    const probClamped = Number.isFinite(probability) ? Math.max(0, Math.min(1, probability)) : 0;
    return {
      fillColor: getRedGradient(probClamped),
      color: getRedGradient(probClamped),
      weight: 1,
      fillOpacity: 0.6,
      smoothFactor: 0.5
    };
  };

  // Popup content for each feature (matches notebook format, with error margin if present)
  const onEachFeature = (feature, layer) => {
    if (feature.properties) {
      const props = feature.properties;
      const crimeType = props.crime_type ?? props.crime_type_display ?? props['crime type'] ?? 'All';
      const crimeTypeInfo = crimeType && crimeType !== 'All' ?
        `<hr style='margin: 5px 0; border: none; border-top: 1px solid #ddd;'/>` +
        `<b>Tipo de Crime Mais Provável:</b> <span style='color: #e74c3c; font-weight: bold;'>${crimeType}</span><br/>` : '';
      const probability = Number(props.probability ?? props.crime_probability ?? props.normalized_prob ?? 0);
      const predictedDaily = Number(props.predicted_daily_avg ?? props.predicted_daily ?? props.daily_avg ?? 0);
      const predictedTotal = Number(props.predicted_total ?? props.total_prediction ?? props.predicted_total ?? 0);
      const nDays = Number(props.n_days ?? props.n_days_forecast ?? 7) || 7;
      const cellId = String(props.h3_cell ?? props.h3 ?? props.cell ?? 'unknown');
      // Error margin (if present)
      const weekly_mae = props.weekly_mae ?? null;
      const prediction_lower = weekly_mae ? Math.max(0, predictedTotal - weekly_mae) : null;
      const prediction_upper = weekly_mae ? predictedTotal + weekly_mae : null;
      const prediction_lower_95 = weekly_mae ? Math.max(0, predictedTotal - 2 * weekly_mae) : null;
      const prediction_upper_95 = weekly_mae ? predictedTotal + 2 * weekly_mae : null;
      const model_r2_test = props.model_r2_test ?? null;
      const model_mae_test = props.model_mae_test ?? null;
      let errorHtml = '';
      if (weekly_mae) {
        errorHtml = `
          <hr style='margin: 5px 0; border: none; border-top: 1px solid #ddd;'/>
          <b>Margem de Erro (MAE):</b> ±${weekly_mae.toFixed(2)} crimes<br/>
          <b>Intervalo 68%:</b> ${prediction_lower.toFixed(2)} - ${prediction_upper.toFixed(2)}<br/>
          <b>Intervalo 95%:</b> ${prediction_lower_95.toFixed(2)} - ${prediction_upper_95.toFixed(2)}<br/>
          <hr style='margin: 5px 0; border: none; border-top: 1px solid #aaa;'/>
          <span style='font-size: 10px; color: #666;'>Modelo R²: ${model_r2_test?.toFixed(3) ?? ''} | MAE Teste: ${model_mae_test?.toFixed(4) ?? ''}</span>
        `;
      }
      const popupContent = `
        <div style='
          font-family: Arial, sans-serif; 
          font-size: 12px; 
          background-color: #111111;
          color: rgba(255,255,255,0.85);
          padding: 10px;
          border-radius: 6px;
        '>
          <b style='font-size: 14px;'>Previsão de Ocorrência de Crime</b><br/>
          <hr style='margin: 5px 0; border: none; border-top: 1px solid #3c3c3c;'/>
          <b>Célula:</b> ${cellId.substring(0, 8)}...<br/>
          <b>Probabilidade:</b> ${(probability * 100).toFixed(1)}%<br/>
          <b>Período:</b> ${nDays} dias<br/>
          ${crimeTypeInfo}
          <hr style='margin: 5px 0; border: none; border-top: 1px solid #3c3c3c;'/>
          <b>Média Diária Prevista:</b> ${predictedDaily.toFixed(3)}/dia<br/>
          <b>Total Previsto:</b> ${predictedTotal.toFixed(1)} crimes<br/>
          ${errorHtml}
          <span style='font-size: 10px; color: #999;'>Método: Poisson (P ≥ 1 crime/dia)</span>
        </div>
      `;

      layer.bindPopup(popupContent);
      // Tooltip on hover
      const tooltipText = crimeType && crimeType !== 'All' ?
        `${crimeType}: ${(probability * 100).toFixed(1)}%` :
        `Probabilidade: ${(probability * 100).toFixed(1)}%`;
      layer.bindTooltip(tooltipText, {
        sticky: true
      });
    }
  };

  // Build overlays for crime types (for layer control)
  const crimeTypeOverlays = useMemo(() => {
    if (!forecastData || !forecastData.features) return [];
    const allFeatures = forecastData.features;
    
    // Build map: crimeType -> features
    const crimeTypeMap = {};
    allFeatures.forEach(feature => {
      const p = feature.properties || {};
      const crimeType = p.crime_type ?? p.crime_type_display ?? p['crime type'] ?? 'All';
      if (!crimeTypeMap[crimeType]) crimeTypeMap[crimeType] = [];
      crimeTypeMap[crimeType].push(feature);
    });
    
    // Always add "All" layer showing all features
    crimeTypeMap['All'] = allFeatures;
    
    // Sort crime types: All first, then by count desc
    const sortedTypes = Object.keys(crimeTypeMap).sort((a, b) => {
      if (a === 'All') return -1;
      if (b === 'All') return 1;
      return crimeTypeMap[b].length - crimeTypeMap[a].length;
    });
    
    // Build overlays
    return sortedTypes.map(type => {
      const features = crimeTypeMap[type];
      const overlayName = type === 'All' ? 'Todos os Tipos' : `🔍 ${type}`;
      return (
        <LayersControl.Overlay key={type} checked={type === 'All'} name={overlayName}>
          <GeoJSON
            key={type + features.length}
            data={{ type: 'FeatureCollection', features }}
            style={styleFeature}
            onEachFeature={onEachFeature}
          />
        </LayersControl.Overlay>
      );
    });
  }, [forecastData]);

  // Summary statistics panel
  const renderSummary = () => {
    if (!forecastData || !forecastData.metadata) return null;

    const { metadata } = forecastData;
    const stats = metadata.statistics;

    // Get crime type distribution
    const crimeTypeCounts = {};
    if (forecastData.features) {
      forecastData.features.forEach(feature => {
        const crimeType = feature.properties?.crime_type || 'All';
        crimeTypeCounts[crimeType] = (crimeTypeCounts[crimeType] || 0) + 1;
      });
    }

    return (
      <Box
        sx={{
          position: 'absolute',
          bottom: 20,
          right: 20,
          zIndex: 1000,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          color: 'white',
          padding: 2,
          borderRadius: 2,
          minWidth: 280,
          fontSize: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
        }}
      >
        <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1 }}>
          Estatísticas de Probabilidade de Crimes
        </Typography>
        
        <Typography variant="body2" sx={{ mb: 0.5 }}>
          <b>Período:</b> {metadata.forecast_period?.start || 'N/A'} a {metadata.forecast_period?.end || 'N/A'}
        </Typography>
        
        <Typography variant="body2" sx={{ mb: 0.5 }}>
          <b>Células exibidas:</b> {metadata.total_cells?.toLocaleString() || 0}
        </Typography>
        
        <hr style={{ margin: '8px 0', border: 'none', borderTop: '1px solid #555' }} />
        
        <Typography variant="body2" sx={{ mb: 0.5 }}>
          <b>Probabilidade média:</b> {(stats?.mean_probability * 100)?.toFixed(1) || 'N/A'}%
        </Typography>
        
        <Typography variant="body2" sx={{ mb: 0.5 }}>
          <b>Probabilidade mediana:</b> {(stats?.median_probability * 100)?.toFixed(1) || 'N/A'}%
        </Typography>
        
        <Typography variant="body2" sx={{ mb: 0.5 }}>
          <b>Células de alto risco (&gt;80%):</b> {stats?.high_risk_cells || 0}
        </Typography>
        
        {Object.keys(crimeTypeCounts).length > 1 && (
          <>
            <hr style={{ margin: '8px 0', border: 'none', borderTop: '1px solid #555' }} />
            <Typography variant="body2" sx={{ mb: 0.5, fontSize: '11px' }}>
              <b>Distribuição por Tipo:</b>
            </Typography>
            {Object.entries(crimeTypeCounts)
              .filter(([type]) => type !== 'All')
              .sort(([,a], [,b]) => b - a)
              .slice(0, 3)
              .map(([type, count]) => (
                <Typography key={type} variant="body2" sx={{ mb: 0.5, fontSize: '11px', pl: 1 }}>
                  • {type}: {count}
                </Typography>
              ))}
          </>
        )}
        
        <hr style={{ margin: '8px 0', border: 'none', borderTop: '1px solid #555' }} />
        
        <Typography variant="body2" sx={{ mb: 0.5 }}>
          <b>Total previsto:</b> {stats?.total_predicted_crimes?.toFixed(0) || 'N/A'} crimes
        </Typography>
        
        <Typography variant="body2">
          <b>Modelo:</b> {metadata.model_version || 'N/A'}
        </Typography>

        <Typography variant="caption" sx={{ display: 'block', mt: 1, color: '#aaa' }}>
          Método: Poisson (P ≥ 1 crime/dia)
        </Typography>
      </Box>
    );
  };

    // Remove filter box (now handled by layer control)

  // Render loading state
  if (loading) {
    return (
      <Box
        sx={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#1a1a1a'
        }}
      >
        <CircularProgress size={60} sx={{ color: '#7011ff' }} />
        <Typography variant="h6" sx={{ mt: 2, color: 'white' }}>
          Carregando previsões...
        </Typography>
        <Typography variant="body2" sx={{ mt: 1, color: '#aaa' }}>
          Carregando dados pré-computados do servidor
        </Typography>
      </Box>
    );
  }

  // Render error state
  if (error) {
    return (
      <Box
        sx={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#1a1a1a',
          padding: 3
        }}
      >
        <Alert severity="error" sx={{ maxWidth: 500 }}>
          <Typography variant="h6">Erro ao Carregar Previsões</Typography>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Box>
    );
  }

  // Render empty state
  if (!forecastData) {
    return (
      <Box
        sx={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#1a1a1a'
        }}
      >
        <Typography variant="h5" sx={{ color: 'white', mb: 2 }}>
          Nenhuma previsão disponível
        </Typography>
        <Typography variant="body1" sx={{ color: '#aaa' }}>
          Verifique se o servidor está rodando e se há dados de previsão
        </Typography>
      </Box>
    );
  }

  // Collapsible legend using React state (moved to top of component)
 const legendBox = (
  <Box
    sx={{
      position: "fixed",
      bottom: 10,
      right: 10,
      width: 340,
      backgroundColor: "#111111",
      border: "1px solid #3c3c3c",
      zIndex: 9999,
      fontSize: 13,
      boxShadow: "2px 2px 6px rgba(0,0,0,0.3)",
      borderRadius: "5px",
    }}
  >
    {/* Cabeçalho clicável */}
    <Box
      sx={{
        padding: "10px 12px",
        backgroundColor: "#111111",
        cursor: "pointer",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        borderRadius: "5px",
      }}
      onClick={() => setLegendCollapsed((c) => !c)}
    >
      <Typography sx={{ fontWeight: "bold", margin: 0, color: "rgba(255,255,255,0.7)" }}>
        Previsão de Probabilidade de Crime
      </Typography>

      <Typography sx={{ fontSize: 18, fontWeight: "bold", color: "rgba(255,255,255,0.7)" }}>
        {legendCollapsed ? "+" : "−"}
      </Typography>
    </Box>

    {/* Conteúdo interno (esconde/mostra) */}
    <Box sx={{ padding: 2, display: legendCollapsed ? "none" : "block" }}>
      {/* Escala */}
      <Typography sx={{ margin: "0 0 8px 0", fontWeight: "bold", color: "rgba(255,255,255,0.7)" }}>
        Escala de Probabilidade:
      </Typography>

              <Typography sx={{ margin: "5px 0", color: "rgba(255,255,255,0.7)" }}>
          <HexagonTwoToneIcon sx={{ color: "#ffc8c8", fontSize: 25, verticalAlign: "middle" }} /> Baixa
        </Typography>

        <Typography sx={{ margin: "5px 0", color: "rgba(255,255,255,0.7)" }}>
          <HexagonTwoToneIcon sx={{ color: "#ff6464", fontSize: 25, verticalAlign: "middle" }} /> Média
        </Typography>

        <Typography sx={{ margin: "5px 0", color: "rgba(255,255,255,0.7)" }}>
          <HexagonTwoToneIcon sx={{ color: "#8b0000", fontSize: 25, verticalAlign: "middle" }} /> Alta
        </Typography>


      <Divider sx={{ borderColor: "#3c3c3c", my: 1 }} />

      <Typography sx={{ margin: "5px 0", fontSize: 11, color: "rgba(255,255,255,0.7)" }}>
        <b>Período de Previsão:</b> 7 dias
      </Typography>

      <Typography sx={{ margin: "5px 0", fontSize: 11, color: "rgba(255,255,255,0.7)" }}>
        <b>Método:</b> Poisson (P ≥ 1 crime/dia)
      </Typography>

      <Typography sx={{ margin: "5px 0", fontSize: 11, color: "rgba(255,255,255,0.7)" }}>
        <b>Agregação:</b> Semanal (H3 Res 10)
      </Typography>

      <Typography sx={{ margin: "5px 0", fontSize: 11, color: "rgba(255,255,255,0.7)" }}>
        <b>Filtro:</b> Probabilidade &gt; 10%
      </Typography>

      <Divider sx={{ borderColor: "#3c3c3c", my: 1 }} />

      <Typography sx={{ margin: "5px 0", fontSize: 11, color: "rgba(255,255,255,0.7)" }}>
        <b>Margem de Erro (MAE):</b> ±X crimes/semana
      </Typography>

      <Typography sx={{ margin: "5px 0", fontSize: 11, color: "rgba(255,255,255,0.7)" }}>
        <b>R² do Modelo:</b> X
      </Typography>

      <Divider sx={{ borderColor: "#3c3c3c", my: 1 }} />

      <Typography sx={{ margin: "5px 0", fontSize: 11, fontWeight: "bold", color: "#2ecc71" }}>
        🔍 Use o controle de camadas (canto superior direito)
      </Typography>

      <Typography
        sx={{ margin: "5px 0", fontSize: 10, color: "rgba(255,255,255,0.7)", fontStyle: "italic" }}
      >
        Filtre por tipo de crime específico
      </Typography>

      <Divider sx={{ borderColor: "#3c3c3c", my: 1 }} />

      <Typography
        sx={{ margin: "5px 0", fontSize: 11, fontWeight: "bold", color: "#e74c3c" }}
      >
        ⚠️ Apenas Previsões (sem dados reais)
      </Typography>

      <Typography
        sx={{ margin: "5px 0", fontSize: 10, color: "rgba(255,255,255,0.7)", fontStyle: "italic" }}
      >
        Clique nas células para ver intervalos de confiança e tipo de crime
      </Typography>

    </Box>
  </Box>
);


  // Render map with predictions and all tile layers, overlays, and legend
  return (
    <Box sx={{ width: '100%', height: '100%', position: 'relative', backgroundColor:"Black",}}>
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        style={{ width: '100%', height: '100%' }}
        zoomControl={true}
        attributionControl={false}
      >
        <LayersControl position="topright" collapsed={true}>
          <LayersControl.BaseLayer name="CartoDB Voyager (HD)">
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              maxZoom={20}
              maxNativeZoom={20}
              subdomains="abcd"
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="OpenStreetMap">
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              maxZoom={19}
              maxNativeZoom={19}
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="CartoDB Positron">
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              maxZoom={20}
              maxNativeZoom={20}
              subdomains="abcd"
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer checked name="CartoDB Dark Matter">
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              maxZoom={20}
              maxNativeZoom={20}
              subdomains="abcd"
            />
          </LayersControl.BaseLayer>
          {/* Crime type overlays */}
          {crimeTypeOverlays}
        </LayersControl>
        {forecastData && (
          <MapBoundsUpdater geojson={forecastData} />
        )}
      </MapContainer>
      {/* Collapsible legend overlay (matches notebook) */}
      {legendBox}
    </Box>
  );
}
