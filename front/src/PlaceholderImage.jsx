import { useState, useEffect } from "react";
import { Box, GlobalStyles } from "@mui/material";
import HomeAppBar from "./HomeAppBar.jsx";
import CrimeMap from "./CrimeMap.jsx";

// Use environment variable for API URL, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export default function PlaceholderImage() {
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load forecast data on component mount
  useEffect(() => {
    const loadForecastData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        console.log('Loading pre-computed forecast data...');
        
        const response = await fetch(`${API_BASE_URL}/api/forecast`);
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || `Server error: ${response.status}`);
        }

        const data = await response.json();
        console.log('Received forecast data:', data.metadata);
        setForecastData(data);
        
      } catch (err) {
        console.error('Forecast loading error:', err);
        setError(err.message || 'Failed to load forecast data. Make sure the API server is running.');
      } finally {
        setLoading(false);
      }
    };

    loadForecastData();
  }, []);

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
          forecastData={forecastData} 
          loading={loading} 
          error={error}
        />
      </Box>
    </>
  );
}
