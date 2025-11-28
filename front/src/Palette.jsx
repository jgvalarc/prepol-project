import { createTheme } from "@mui/material/styles";

// Cores extraídas do seu código HomeAppBar:
// Fundo da Sidebar: #090909
// Destaque Principal (Vermelho): #ff0000
// Destaque Secundário (Roxo): #800080
// Cor do Texto: #fff
// Cor do Divisor: grey

const theme = createTheme({
  palette: {
    // 1. Cor de Destaque Principal (Vermelho)
    primary: {
      main: "#a10000ff", 
      dark: "#650000", 
      contrastText: "#ffffff",
    },
    
    // 🎯 2. NOVA COR DESTAQUE (Roxo) - Usado como base do gradiente
    secondary: {
        main: "#800080", // Roxo
        light: "#993399", // Roxo um pouco mais claro (para uso opcional)
        dark: "#660066", // Roxo mais escuro (para uso opcional)
        contrastText: "#ffffff",
    },
    
    // 3. Cores do Fundo e Superfície
    background: {
      default: "#090909", 
      paper: "#090909", 
    },
    
    // 4. Cores de Texto
    text: {
      primary: "#ffffff", 
      secondary: "rgba(255, 255, 255, 0.7)", 
    },
    
    // 5. Cores de Ação (Hover, Seleção)
    action: {
      hover: "rgba(255, 255, 255, 0.05)", 
      selected: "#ff0000", // Mantém o vermelho para seleção
    },
    
    // 6. Cor do Divisor
    divider: "grey", 
  },
  
  // Opcional: Configurar componentes para usar essas cores
  components: {
    MuiListItemButton: {
      styleOverrides: {
        root: ({ theme }) => ({
          "&:hover": {
             backgroundColor: theme.palette.action.hover,
          },
        }),
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          backgroundColor: "grey",
        },
      },
    },
  },
});

export default theme;