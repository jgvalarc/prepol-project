import { Box, Typography, GlobalStyles } from "@mui/material";
import PixelBlast from './Components/PixelBlast';
import HomeAppBar from "./HomeAppBar";

// Largura da HomeAppBar (assumida como 60px)
const collapsedWidth = 60;

export default function NewHome() {
  return (
    <>
      <GlobalStyles
        styles={{
          "html, body": {
            margin: 0,
            padding: 0,
            width: "100%",
            height: "100%",
            backgroundColor: "#0F0C16",
            overflow: "hidden",
          },
          "#root": {
            width: "100%",
            minHeight: "100%",
          },
        }}
      />

      {/* Barra Lateral */}
      <HomeAppBar />

      {/* Background */}
      <Box
        sx={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          zIndex: 0,
          backgroundColor: "#0d0d0d",
        }}
      >
        <PixelBlast />
      </Box>

      {/* Conteúdo Principal */}
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          width: "100%",
          height: "100vh",
          color: "white",
          position: "relative",
          zIndex: 1,
          backgroundColor: "transparent",
          bottom: 200,
        }}
      >

        {/* Bloco do Cabeçalho */}
        <Box
          component="main"
          sx={{
            width: `calc(100% - ${collapsedWidth}px)`,
            marginLeft: `${collapsedWidth}px`,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            textAlign: "center",
            maxWidth: "1000px",
            mx: "auto",
          }}
        >

          {/* Título Principal */}
          <Typography
            variant="h2"
            component="h1"
            noWrap
            sx={{
              fontWeight: 600,
              fontSize: { xs: "1.6rem", sm: "2.2rem", md: "2.8rem", lg: "3.2rem" },
              lineHeight: 1.15,
              letterSpacing: "-0.02em",
              color: "white",
              marginBottom: "1rem", // 🔹 Reduz espaço entre os textos
            }}
          >
            <Box
              component="span"
              sx={{
                background: "linear-gradient(90deg, #FF00CC 0%, #aa44ff 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                display: "inline-block",
                paddingBottom: "0.1em",
                marginBottom: "-0.1em",
              }}
            >
              O futuro
            </Box>
            {" "}começa com informação.
          </Typography>

        </Box>

        {/* Texto de Apoio */}
        <Typography
          sx={{
            fontSize: { xs: "1.05rem", sm: "1.15rem", md: "1.25rem", lg: "1.3rem" },
            fontWeight: 400,
            lineHeight: 1.4,
            maxWidth: "650px",
            marginTop: "0",             // 🔹 Remove excesso de espaço
            color: "rgba(255,255,255,0.9)",
            textAlign: "center",
          }}
        >O PREPOL possibilita prever ocorrências criminais com base em dados reais,
          oferecendo análises precisas e mapas dinâmicos de risco. Projetado para
          auxiliar na tomada de decisões.
        </Typography>

      </Box>
    </>
  );
}
