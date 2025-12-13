import React from 'react';
import { Box, Typography, Paper, Divider } from "@mui/material";

// Paleta de cores baseada no seu estilo
const colors = {
  primaryMain: "#bf0000",
  bgPaper: "rgba(30, 30, 30, 0.7)", // Fundo escuro semi-transparente
  textPrimary: "#ffffff",
  textSecondary: "rgba(255, 255, 255, 0.7)",
  divider: "#a10000ff", // Vermelho
};

export function FeatureCard({ title, content }) {
  return (
    <Paper
      elevation={8}
      sx={{
        borderRadius: 3,
        padding: 3,
        height: '100%', // Essencial para o Grid esticar a altura
        backgroundColor: colors.bgPaper,
        border: `1px solid ${colors.divider}`,
        backdropFilter: "blur(5px)", // Efeito de desfoque sutil
        display: "flex",
        flexDirection: "column",
        transition: 'transform 0.3s',
        '&:hover': {
            transform: 'translateY(-5px)', // Pequeno efeito de elevação no hover
            boxShadow: `0 10px 20px ${colors.divider}80`,
        }
      }}
    >
      <Typography 
        variant="h5" 
        component="h3" 
        sx={{ 
          color: colors.primaryMain, 
          fontWeight: 700,
          marginBottom: 1 
        }}
      >
        {title}
      </Typography>
      
      <Divider sx={{ 
          bgcolor: colors.divider, 
          width: '50px', 
          height: '3px', 
          mb: 2 
      }} />

      <Typography 
        variant="body1" 
        sx={{ 
          color: colors.textSecondary, 
          lineHeight: 1.6 
        }}
      >
        {content}
      </Typography>
    </Paper>
  );
}