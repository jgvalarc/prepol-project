import { useState } from "react";
import { Box, GlobalStyles } from "@mui/material";
import MapAppBar from "./MapAppBar.jsx";
import HomeAppBar from "./HomeAppBar.jsx";
import CrimeMap from "./CrimeMap.jsx";

// Use environment variable for API URL, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export default function PlaceholderImage() {
  const [predictionData, setPredictionData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleApplyFilters = async (filters) => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Fetching predictions for:', filters);
      
      const response = await fetch(`${API_BASE_URL}/api/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_date: filters.startDate,
          end_date: filters.endDate
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Server error: ${response.status}`);
      }

      const data = await response.json();
      console.log('Received prediction data:', data.summary);
      setPredictionData(data);
      
    } catch (err) {
      console.error('Prediction error:', err);
      setError(err.message || 'Failed to fetch predictions. Make sure the API server is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <HomeAppBar position="fixed" />
      <GlobalStyles
        styles={{
          "html, body, #root": {
            margin: 0,
            padding: 0,
            width: "100%",
            height: "100%",
            overflow: "hidden",
          },
        }}
      />
      
      {/* Page container */}
      <Box
        sx={{
          width: "100vw",
          height: "100vh",
          backgroundColor: "#1a1a1a",
          pt: "0px", // Remove padding - map fills screen
          position: "relative"
        }}
      >
        {/* Crime Map Component */}
        <CrimeMap 
          predictionData={predictionData} 
          loading={loading} 
          error={error}
        />
        
        {/* Map Controls Overlay */}
        <MapAppBar onApplyFilters={handleApplyFilters} />
      </Box>
    </>
  );
}
