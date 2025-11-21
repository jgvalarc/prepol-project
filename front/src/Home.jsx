import { Box, Typography, GlobalStyles } from "@mui/material";
import HomeAppBar from "./HomeAppBar.jsx";
//import DarkVeil from "./DarkVeil";
import FloatingLines from './Components/FloatingLines';


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
            backgroundColor: "transparent", // deixa escuro atrás do DarkVeil
            overflow: "hidden", // previne scroll causado pelo background animado
          },
          "#root": {
            width: "100%",
            height: "100%",
          },
        }}
      />

      {/* 🌌 Fundo DarkVeil ocupando toda a tela sem interferir no layout */}
      <Box
        sx={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          zIndex: -1,        // 🚀 chave: fica atrás de tudo
          pointerEvents: "none", // evita qualquer interferência com cliques
        }}
      >
        <FloatingLines />
      </Box>

      {/* 📦 Conteúdo principal (fica acima do DarkVeil) */}
      <Box
        sx={{
          display: "flex",
          width: "100%",
          minHeight: "100vh",
          color: "white",
          position: "relative",
          zIndex: 1,  // garante que todos os componentes fiquem acima
          backgroundColor: "transparent",
        }}
      >
        <HomeAppBar />

        <Box
          sx={{
            flexGrow: 1,
            marginLeft: "60px",
            minHeight: "100vh",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Typography variant="h3" sx={{ mb: 2 }}>
            Preveja o risco. Proteja-se com informação.
          </Typography>

          <Typography variant="body1" sx={{ color: "#aaa" }}>
            PREPOL
          </Typography>
        </Box>
      </Box>
    </>
  );
}
