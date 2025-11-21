import { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet';
import { Box, CircularProgress, Typography, Alert } from '@mui/material';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

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

export default function CrimeMap({ predictionData, loading, error }) {
  const [mapCenter] = useState([-8.05, -34.9]); // Recife, Brazil
  const [mapZoom] = useState(11);

  // Color gradient function (light red -> dark red)
  const getRedGradient = (normalizedValue) => {
    // RGB: (255, 200, 200) -> (139, 0, 0)
    const r = Math.floor(255 - (116 * normalizedValue));
    const g = Math.floor(200 - (200 * normalizedValue));
    const b = Math.floor(200 - (200 * normalizedValue));
    return `rgb(${r}, ${g}, ${b})`;
  };

  // Style function for GeoJSON features
  const styleFeature = (feature) => {
    if (!feature || !feature.properties) return {};

    const probability = feature.properties.probability || 0;

    return {
      fillColor: getRedGradient(probability),
      weight: 1,
      opacity: 1,
      color: getRedGradient(probability),
      fillOpacity: 0.6
    };
  };

  // Popup content for each feature
  const onEachFeature = (feature, layer) => {
    if (feature.properties) {
      const props = feature.properties;
      const popupContent = `
        <div style="font-family: Arial, sans-serif; font-size: 12px;">
          <b style="font-size: 14px;">Probabilidade de Ocorrência de Crime</b><br/>
          <hr style="margin: 5px 0; border: none; border-top: 1px solid #ddd;"/>
          <b>Célula:</b> ${props.h3_cell.substring(0, 8)}...<br/>
          <b>Probabilidade:</b> ${(props.probability * 100).toFixed(1)}%<br/>
          <b>Período:</b> ${props.n_days} dias<br/>
          <hr style="margin: 5px 0; border: none; border-top: 1px solid #ddd;"/>
          <b>Média Diária Prevista:</b> ${props.predicted_daily_avg.toFixed(3)}/dia<br/>
          <b>Total Previsto:</b> ${props.predicted_total.toFixed(1)}<br/>
          <b>Total Real:</b> ${props.actual_total}<br/>
          <b>Erro de Predição:</b> ${Math.abs(props.predicted_total - props.actual_total).toFixed(1)}
        </div>
      `;
      layer.bindPopup(popupContent);

      // Tooltip on hover
      layer.bindTooltip(`Probabilidade: ${(props.probability * 100).toFixed(1)}%`, {
        sticky: true
      });
    }
  };

  // Memoize GeoJSON layer to prevent unnecessary re-renders
  const geoJsonLayer = useMemo(() => {
    if (!predictionData || !predictionData.geojson) return null;

    return (
      <GeoJSON
        key={JSON.stringify(predictionData.geojson)} // Force re-render on data change
        data={predictionData.geojson}
        style={styleFeature}
        onEachFeature={onEachFeature}
      />
    );
  }, [predictionData]);

  // Summary statistics panel
  const renderSummary = () => {
    if (!predictionData || !predictionData.summary) return null;

    const { summary } = predictionData;
    const stats = summary.statistics;

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
          <b>Período:</b> {summary.date_range.start} a {summary.date_range.end} ({summary.date_range.days} dias)
        </Typography>
        
        <Typography variant="body2" sx={{ mb: 0.5 }}>
          <b>Células exibidas:</b> {summary.displayed_cells.toLocaleString()} de {summary.total_cells.toLocaleString()}
        </Typography>
        
        <hr style={{ margin: '8px 0', border: 'none', borderTop: '1px solid #555' }} />
        
        <Typography variant="body2" sx={{ mb: 0.5 }}>
          <b>Probabilidade média:</b> {(stats.mean_probability * 100).toFixed(1)}%
        </Typography>
        
        <Typography variant="body2" sx={{ mb: 0.5 }}>
          <b>Probabilidade mediana:</b> {(stats.median_probability * 100).toFixed(1)}%
        </Typography>
        
        <Typography variant="body2" sx={{ mb: 0.5 }}>
          <b>Células de alto risco (&gt;80%):</b> {stats.high_risk_cells}
        </Typography>
        
        <hr style={{ margin: '8px 0', border: 'none', borderTop: '1px solid #555' }} />
        
        <Typography variant="body2" sx={{ mb: 0.5 }}>
          <b>Total previsto:</b> {stats.total_predicted.toFixed(0)} crimes
        </Typography>
        
        <Typography variant="body2">
          <b>Total real:</b> {stats.total_actual} crimes
        </Typography>

        <Typography variant="caption" sx={{ display: 'block', mt: 1, color: '#aaa' }}>
          Método: Poisson (P ≥ 1 crime/dia)
        </Typography>
      </Box>
    );
  };

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
          Gerando predições...
        </Typography>
        <Typography variant="body2" sx={{ mt: 1, color: '#aaa' }}>
          Isso pode levar alguns segundos
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
          <Typography variant="h6">Erro de Predição</Typography>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Box>
    );
  }

  // Render empty state
  if (!predictionData) {
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
          Selecione um intervalo de datas para ver as predições
        </Typography>
        <Typography variant="body1" sx={{ color: '#aaa' }}>
          Use os controles no canto superior direito para configurar sua análise
        </Typography>
      </Box>
    );
  }

  // Render map with predictions
  return (
    <Box sx={{ width: '100%', height: '100%', position: 'relative' }}>
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        style={{ width: '100%', height: '100%' }}
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />
        
        {geoJsonLayer}
        
        {predictionData && predictionData.geojson && (
          <MapBoundsUpdater geojson={predictionData.geojson} />
        )}
      </MapContainer>

      {renderSummary()}
    </Box>
  );
}
