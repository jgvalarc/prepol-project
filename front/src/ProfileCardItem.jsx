import React from "react";
import {
  Box,
  Typography,
  Paper,
  Divider,
  Avatar,
  IconButton,
  Stack
} from "@mui/material";
import { LinkedIn } from "@mui/icons-material"; // Ícone do LinkedIn

// Sua paleta de cores original
const colors = {
  primaryMain: "#a10000ff", // Vermelho principal
  bgPaper: "#111111",       // Fundo escuro do card
  textPrimary: "#ffffff",   // Texto branco
  textSecondary: "rgba(255, 255, 255, 0.7)", // Texto cinza
  divider: "#3c3c3c",
};

// Componente reutilizável para um único Card de Perfil
export function ProfileCardItem({ name, role, desc, image, linkedinUrl }) {
  return (
    <Paper
      elevation={8}
      sx={{
        borderRadius: 4, 
        width: 320, 
        minWidth: 280,
        backgroundColor: colors.bgPaper,
        border: `1px solid ${colors.divider}`,
        overflow: "hidden",
        position: "relative",
        display: "flex",
        flexDirection: "column",
        flexShrink: 0, 
        height: '100%', // Para que todos os cards tenham a mesma altura no Grid
      }}
    >
      {/* 1. Header Vermelho Curvo */}
      <Box
        sx={{
          height: 130,
          width: "100%",
          borderBottomLeftRadius: "50% 40px",
          borderBottomRightRadius: "50% 40px",
        }}
      />

      {/* 2. Imagem Circular (Avatar) */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          mt: "-65px", 
        }}
      >
        <Avatar
          alt={name}
          src={image}
          sx={{
            width: 130,
            height: 130,
            border: `6px solid ${colors.bgPaper}`, 
            boxShadow: "0px 5px 15px rgba(0,0,0,0.5)",
          }}
        />
      </Box>

      {/* 3. Conteúdo do Card */}
      <Box sx={{ p: 3, textAlign: "center" }}>
        <Typography
          variant="h5"
          sx={{
            color: colors.textPrimary,
            fontWeight: "bold",
            mb: 0.5,
          }}
        >
          {name}
        </Typography>

        <Typography
          variant="subtitle1"
          sx={{
            color: colors.primaryMain,
            fontWeight: "600",
            mb: 2,
            textTransform: "uppercase",
            fontSize: "0.85rem",
            letterSpacing: 1
          }}
        >
          {role}
        </Typography>

        {/* Divisor Vermelho Pequeno */}
        <Divider
          sx={{
            width: "90%",
            borderBottomWidth: 1,
            borderColor: "#3c3c3c",
            margin: "0 auto 20px auto", 
            borderRadius: 2
          }}
        />

        {/* Descrição */}
        <Typography
          variant="body2"
          sx={{
            color: colors.textSecondary,
            lineHeight: 1.6,
            mb: 3,
            // Garante que o texto se alinhe uniformemente
            flexGrow: 1 
          }}
        >
          {desc}
        </Typography>

        {/* Ícone do LinkedIn */}
        <Stack direction="row" spacing={2} justifyContent="center" sx={{ mt: 'auto' }}>
            <IconButton 
                component="a" 
                href={linkedinUrl} 
                target="_blank" 
                disabled={!linkedinUrl} // Desabilita se o link for vazio
                sx={{ 
                    color: colors.primaryMain, 
                    '&:hover': { color: '#ff0000' },
                    ...(linkedinUrl ? {} : { opacity: 0.4 }) // Estilo para desabilitado
                }}
            >
              <LinkedIn fontSize="large" /> 
            </IconButton>
        </Stack>
      </Box>
    </Paper>
  );
}