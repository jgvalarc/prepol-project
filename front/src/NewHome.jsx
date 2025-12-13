import { Box, Typography, GlobalStyles, Divider, } from "@mui/material";
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import PublicIcon from '@mui/icons-material/Public';
import BoltIcon from '@mui/icons-material/Bolt';
import PixelBlast from './Components/PixelBlast';
import HomeAppBar from "./HomeAppBar";

// Largura da HomeAppBar (assumida como 60px)
const collapsedWidth = 60;

// --- Componente de Card Reutilizável ---
const FeatureCard = ({ icon, title, description }) => (
  <Box
    sx={{
      // Estilos do Card (fundo escuro com bordas arredondadas)
      backgroundColor: '#111111', // Fundo mais escuro e sutilmente transparente
      backdropFilter: 'blur(5px)', // Efeito de desfoque sutil
      borderRadius: '16px',
      padding: '24px',
      maxWidth: '300px',
      minHeight: '200px',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'flex-start',
      alignItems: 'flex-start',
      margin: '16px',
      boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.15)', // Sombra para profundidade
      border: '1px solid rgba(255, 255, 255, 0.05)', // Borda sutil
      transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
      '&:hover': {
        transform: 'translateY(-5px)', // Efeito de levantamento no hover
        boxShadow: '0 12px 40px 0 rgba(0, 0, 0, 0.3)',
      },
    }}
  >
    {/* Ícone */}
    <Box
  sx={{
    color: '#bf0000',
    fontSize: '3rem',
    marginBottom: '16px',
    width: '100%',
    display: 'flex',
    justifyContent: 'center',
  }}
>
  {icon}
</Box>

    <Divider
  sx={{
    width: '100%',
    marginBottom: '16px',
    borderColor: 'rgba(255,255,255,0.1)',
  }}
/>

    {/* Título */}
    <Typography 
      variant="h6" 
      component="h3" 
      sx={{ 
        fontWeight: 600, 
        color: 'white', 
        marginBottom: '8px' 
      }}
    >
      {title}
    </Typography>
    
    {/* Descrição */}
    <Typography 
      variant="body2" 
      sx={{ 
        color: 'rgba(255, 255, 255, 0.7)', 
        lineHeight: 1.5,
        fontSize: '0.9rem'
      }}
    >
      {description}
    </Typography>
  </Box>
);

// --- Componente Principal ---
export default function NewHome() {
  
  // Textos fornecidos para os Cards
  const cardData = [
    {
      icon: <AutoAwesomeIcon fontSize="inherit" />,
      title: "Inteligência Preditiva",
      description: "O PrePol utiliza machine learning para transformar dados históricos de ocorrências criminais em mapas probabilísticos de risco, prevendo o espaço-tempo de eventos futuros.",
    },
    {
      icon: <BoltIcon fontSize="inherit" />,
      title: "Viabilidade e Performance",
      description: "A viabilidade técnica foi comprovada com R² de até 0,93 em um protótipo funcional. O mapa pré-computado sobre mais de 50 mil unidades espaciais garante alta confiabilidade e baixo custo operacional.",
    },
    {
      icon: <PublicIcon fontSize="inherit" />,
      title: "Escalabilidade e Mercado",
      description: "A solução é altamente escalável para outros municípios e estados, sem alteração estrutural. Os mercados potenciais incluem gestões públicas, consórcios metropolitanos, e empresas de urbanismo e seguros.",
    },
  ];

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
          // Ajuste para empurrar o conteúdo mais para cima e centralizar melhor
          justifyContent: "flex-start", 
          alignItems: "center",
          width: "100%",
          height: "100vh",
          color: "white",
          position: "relative",
          zIndex: 1,
          backgroundColor: "transparent",
          paddingTop: 'calc(100vh / 4 - 80px)', // Centraliza verticalmente de forma adaptada
        }}
      >
        {/* Bloco do Cabeçalho e Texto de Apoio */}
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
            paddingX: { xs: '20px', md: '0' },
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
              marginBottom: "1rem",
            }}
          >
            <Box
              component="span"
              sx={{
                background: "linear-gradient(90deg, #bf0000 0%, #800000 100%)",
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

          {/* Texto de Apoio */}
          <Typography
            sx={{
              fontSize: { xs: "1.05rem", sm: "1.15rem", md: "1.25rem", lg: "1.3rem" },
              fontWeight: 400,
              lineHeight: 1.4,
              maxWidth: "650px",
              marginTop: "0",
              color: "rgba(255,255,255,0.9)",
              textAlign: "center",
              marginBottom: '32px',
            }}
          >O PREPOL possibilita prever ocorrências criminais com base em dados reais,
            oferecendo análises precisas e mapas dinâmicos de risco. Projetado para
            auxiliar na tomada de decisões.
          </Typography>
          
          {/* --- Container dos Cards --- */}
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', md: 'row' }, // Coluna em telas pequenas, linha em telas maiores
              justifyContent: 'center',
              alignItems: 'center',
              width: '100%',
              marginTop: 7,
              paddingX: '20px',
            }}
          >
            {cardData.map((card, index) => (
              <FeatureCard 
                key={index}
                icon={card.icon}
                title={card.title}
                description={card.description}
              />
            ))}
          </Box>
          {/* --- Fim do Container dos Cards --- */}

        </Box>

      </Box>
    </>
  );
}