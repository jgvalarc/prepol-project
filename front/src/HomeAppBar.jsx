import {
  Box,
  Toolbar,
  Typography,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Tooltip,
  IconButton,
} from "@mui/material";

import Logo from "./assets/Logo.png";


import { Link } from "react-router-dom";
// Ícones de navegação
import HomeIcon from '@mui/icons-material/Home';
import MapIcon from '@mui/icons-material/Map';
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import InfoIcon from '@mui/icons-material/Info';
import LogoutIcon from '@mui/icons-material/Logout';

// Largura FIXA da barra lateral (sempre recolhida)
// Mantemos a constante para DRY (Não se Repetir) e clareza.
const collapsedWidth = 60; 

// 🎨 CORES LITERAIS (Definidas para o gradiente e a aparência)
const GRADIENT_TOP_COLOR = "#800000"; 
const GRADIENT_BOTTOM_COLOR = "#FF0000"; 
const SIDEBAR_BG_COLOR = "#111111"; 
const CURRENT_TEXT_COLOR = "#fff"; 
const DIVIDER_COLOR = "#3c3c3c"; 

// 🎯 DEFINIÇÃO DO GRADIENTE VERTICAL
const themeGradientLine = `linear-gradient(to bottom, ${GRADIENT_TOP_COLOR}, ${GRADIENT_BOTTOM_COLOR})`;

// 🎯 ESTILO DE LINHA LATERAL NO HOVER
const lineHoverStyle = {
  position: "relative",
  "&::after": {
    content: '""',
    position: "absolute",
    top: 0,
    left: 0,
    transform: "translateY(0)",
    height: "100%",
    width: 0,
    backgroundImage: themeGradientLine, 
    backgroundSize: '100% 100%',
    borderRadius: "0 4px 4px 0",
    transition: "width 0.3s ease",
    zIndex: 1,
  },
  "&:hover::after": {
    width: "3px", // Espessura da barra no hover
  },
  
  "&:hover": {
    backgroundColor: 'rgba(255, 255, 255, 0.05)', // Fundo sutil no hover
  },
  
  '&.MuiListItemButton-root': {
    position: 'relative',
  }
};

// Itens de navegação
const navItems = [
  { text: "Início", icon: <HomeIcon />, path: "/Home" },
  { text: "Prepol", icon: <MapIcon />, path: "/Map" },
  { text: "Sobre", icon: <InfoIcon />, path: "/About" },
];

export default function HomeAppBar() {
  
  // 🚫 REMOVIDA: const currentWidth = collapsedWidth; 
  // Agora usamos 'collapsedWidth' diretamente

  const backgroundStyle = {
    background: SIDEBAR_BG_COLOR,
  };

  const renderListItem = (item, isProfile = false) => (
    <Tooltip
      title={item.text} 
      placement="right"
      key={item.text}
    >
      <ListItem disablePadding>
        <ListItemButton
          component={Link}
          to={item.path}
          sx={{
            minHeight: 48,
            justifyContent: "center", 
            px: 2.5,
            py: 1.5,
            ...lineHoverStyle,
          }}
        >
          <ListItemIcon
            sx={{
              minWidth: 0,
              mr: "auto", 
              justifyContent: "center",
              color: CURRENT_TEXT_COLOR,
            }}
          >
            {item.icon}
          </ListItemIcon>
        </ListItemButton>
      </ListItem>
    </Tooltip>
  );

  return (
    <Box sx={{ display: "flex" }}>
      {/* 1. Sidebar Fixa e Recolhida */}
      <Box
        sx={{
          // ✅ USANDO A CONSTANTE DIRETAMENTE
          width: collapsedWidth, 
          flexShrink: 0,
          ...backgroundStyle,
          color: CURRENT_TEXT_COLOR,
          height: "100vh",
          position: "fixed",
          display: "flex",
          flexDirection: "column",
          zIndex: 1200,
          overflowX: "hidden",
          borderRight: "1px solid #3c3c3c",
        }}
      >
        {/* 1.1 Header */}
        <Toolbar
          sx={{
            justifyContent: "center", 
            minHeight: "64px !important",
          }}
        >
          <IconButton 
          component={Link}
          to="/Home"
          sx={{ p: 0 }}>
            <Box
              component="img"
              src={Logo}
              alt="Logo"
              sx={{ width: 32, height: 32 }}
            />
          </IconButton>
        </Toolbar>

        {/* DIVIDER */}
        <Divider sx={{ bgcolor: DIVIDER_COLOR, width: "75%", alignSelf: "center", mb: 1,}} />

        {/* 1.2 Lista de Navegação Principal */}
        <List sx={{ flexGrow: 1, p: 0 }}>
          {navItems.map((item) => renderListItem(item))}
        </List>

        {/* 1.3 Rodapé (Settings e Perfil) */}
        <Box sx={{ p: 0, display: "flex", flexDirection: "column", gap: 1, mb: 3, }}>

          {/* NOVA DIVIDER */}
          <Divider sx={{ bgcolor: DIVIDER_COLOR, width: "75%", alignSelf: "center", }} />

          {/* Exemplo de Perfil */}
          {renderListItem({ text: "Sair", icon: <LogoutIcon />, path: "/" })}
        </Box>
      </Box>
      
      {/* 2. O conteúdo principal da aplicação deve usar a margem marginLeft: collapsedWidth para compensar a sidebar. */}
    </Box>
  );
}