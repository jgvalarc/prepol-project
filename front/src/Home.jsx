import { Box, Typography, GlobalStyles, Toolbar } from "@mui/material";
import HomeAppBar from "./HomeAppBar.jsx";
//import DarkVeil from "./DarkVeil"; // Componente não usado/necessário
import PixelBlast from './Components/PixelBlast.jsx';

export default function Home() {
  return (
    <>
      <GlobalStyles
        styles={{
          "html, body": {
            margin: 0,
            padding: 0,
            width: "100%",
            height: "100%",
            // 🛠️ CORREÇÃO 1: Fundo preto explícito para o Orb ser visível
            backgroundColor: "#060505", 
            overflowX: "hidden", // previne scroll horizontal
            overflowY: "auto", // permite scroll vertical se o conteúdo crescer
          },
          "#root": {
            width: "100%",
            minHeight: "100%",
          },
        }}
      />

      {/* 🌌 Fundo com o Orb Animado */}
      {/* Colocado no topo da renderização para garantir que fique por baixo.
        O zIndex: -1 o coloca atrás de TUDO, incluindo o body/html (que agora é preto).
      */}
      <Box
        sx={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          zIndex: 0, // ZIndex 0 ou -1. Usar ZIndex: 0 é mais seguro se o body tiver ZIndex baixo.
          // 🛠️ CORREÇÃO 2: Removido 'pointerEvents: "none"' para permitir interatividade (hover/mouse move)
          // Se o Orb não precisar de interatividade, você pode readicionar: pointerEvents: "none",
        }}
      >
        <PixelBlast />
      </Box>

      {/* 📦 Conteúdo Principal e Sidebar */}
      <Box
        sx={{
          display: "flex",
          width: "100%",
          minHeight: "100vh",
          color: "white",
          position: "relative",
          zIndex: 1, // Garante que todo o conteúdo (sidebar, texto) fique acima do Orb (ZIndex: 0)
          backgroundColor: "transparent", // Garante que o fundo do Orb apareça
        }}
      >
        {/* 1. Sidebar (HomeAppBar) - ZIndex já é alto por ser fixed/sticky */}
        <HomeAppBar />

        {/* 2. Conteúdo da Página */}
        <Box
          component="main" // Boa prática para o conteúdo principal
          sx={{
            flexGrow: 1,
            // 🛠️ Ajuste de Margem: Garante que o conteúdo comece após a sidebar recolhida (60px)
            marginLeft: "60px",
            minHeight: "100vh",
            display: "flex",
            flexDirection: "column",
            p: 3, // Adiciona um padding
          }}
        >
          {/* Adicionando um Toolbar vazio para compensar a barra superior, se necessário. 
             (Geralmente usado quando a app bar é fixa no topo) */}
          <Toolbar />
          
          <Typography variant="h3" sx={{ mb: 2, textAlign: 'center' }}>
            Preveja o risco. Proteja-se com informação.
          </Typography>

          <Typography variant="body1" sx={{ color: "#aaa", textAlign: 'center' }}>
            PREPOL
          </Typography>
        </Box>
      </Box>
    </>
  );
}