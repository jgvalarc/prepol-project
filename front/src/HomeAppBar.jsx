import { useState } from "react";
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

import { Link } from "react-router-dom";
import KeyboardDoubleArrowRightIcon from '@mui/icons-material/KeyboardDoubleArrowRight';
import KeyboardDoubleArrowLeftIcon from '@mui/icons-material/KeyboardDoubleArrowLeft';
import HomeIcon from '@mui/icons-material/Home';
import MapIcon from '@mui/icons-material/Map';
import GroupsIcon from '@mui/icons-material/Groups';
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import SettingsIcon from "@mui/icons-material/Settings";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import InfoIcon from '@mui/icons-material/Info';
import QuizIcon from '@mui/icons-material/Quiz';

// Largura da barra lateral quando aberta e recolhida
const drawerWidth = 240;
const collapsedWidth = 60;

// 🎨 CORES LITERAIS (Definidas para o gradiente e a aparência)
const GRADIENT_TOP_COLOR = "#7011ff"; // Vermelho
const GRADIENT_BOTTOM_COLOR = "#FF0000"; // Roxo
const SIDEBAR_BG_COLOR = "transparent"; // Fundo preto "#090909"
const CURRENT_TEXT_COLOR = "#fff"; // Texto branco
const DIVIDER_COLOR = "grey"; // Divisor cinza

// 🎯 DEFINIÇÃO DO GRADIENTE VERTICAL: Vermelho (topo) para Roxo (base)
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
    
    // Aplicação do Gradiente
    backgroundImage: themeGradientLine, 
    backgroundSize: '100% 100%',
    
    borderRadius: "0 4px 4px 0",
    transition: "width 0.3s ease",
    zIndex: 1,
  },
  "&:hover::after": {
    width: "4px", // Espessura da barra no hover
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
  { text: "Início", icon: <HomeIcon />, path: "/" },
  { text: "Prepol", icon: <MapIcon />, path: "/Map" },
  { text: "Sobre", icon: <GroupsIcon />, path: "/Sobre" },
  { text: "Dicas", icon: <QuizIcon />, path: "/Dicas" },
  { text: "Informação", icon: <InfoIcon />, path: "/Info" },
];

// Item Settings
const settingsItem = { text: "Configurações", icon: <SettingsIcon />, path: "/settings" };

export default function HomeAppBar() {
  const [open, setOpen] = useState(false);

  const toggleDrawer = () => {
    setOpen(!open);
  };

  const currentWidth = open ? drawerWidth : collapsedWidth;

  const backgroundStyle = {
    background: SIDEBAR_BG_COLOR,
  };

  const renderListItem = (item, isProfile = false) => (
    <Tooltip
      title={!open ? item.text : ""}
      placement="right"
      key={item.text}
    >
      <ListItem disablePadding>
        <ListItemButton
          component={Link}
          to={item.path}
          sx={{
            minHeight: 48,
            justifyContent: open ? "initial" : "center",
            px: 2.5,
            py: 1.5,
            ...lineHoverStyle,
            ...(open && {
              textAlign: 'initial',
            }),
          }}
        >
          <ListItemIcon
            sx={{
              minWidth: 0,
              mr: open ? 3 : "auto",
              justifyContent: "center",
              color: CURRENT_TEXT_COLOR,
            }}
          >
            {item.icon}
          </ListItemIcon>
          {open && (
            <ListItemText
              primary={item.text}
              sx={{
                opacity: 1,
                flexGrow: 1,
                textAlign: 'left',
                my: 0,
              }}
            />
          )}
          {open && isProfile && <ChevronRightIcon />}
        </ListItemButton>
      </ListItem>
    </Tooltip>
  );

  return (
    <Box sx={{ display: "flex" }}>
      {/* 1. Sidebar Recolhível/Expansível */}
      <Box
        sx={{
          width: currentWidth,
          flexShrink: 0,
          ...backgroundStyle,
          color: CURRENT_TEXT_COLOR,
          height: "100vh",
          position: "fixed",
          display: "flex",
          flexDirection: "column",
          transition: "width 0.3s ease",
          zIndex: 1200,
          overflowX: "hidden",
        }}
      >
        {/* 1.1 Header e Botão de Recolher */}
        <Toolbar
          sx={{
            justifyContent: open ? "space-between" : "center",
            minHeight: "64px !important",
          }}
        >
          {open && (
            <Typography variant="h6" noWrap component="div">
              PREPOL
            </Typography>
          )}
          <IconButton onClick={toggleDrawer} sx={{ color: CURRENT_TEXT_COLOR }}>
            {open ? <KeyboardDoubleArrowLeftIcon /> : <KeyboardDoubleArrowRightIcon />}
          </IconButton>
        </Toolbar>

        {/* DIVIDER: Usando a cor de divider fixa */}
        <Divider sx={{ bgcolor: DIVIDER_COLOR, width: "75%", alignSelf: "center", mb: 1,}} />

        {/* 1.2 Lista de Navegação Principal */}
        <List sx={{ flexGrow: 1, p: 0 }}>
          {navItems.map((item) => renderListItem(item))}
        </List>

        {/* 1.3 Rodapé (Settings e Perfil) */}
        <Box sx={{ p: 0, display: "flex", flexDirection: "column", gap: 1, mb: 3, }}>

          {/* ITEM: SETTINGS */}
          {renderListItem(settingsItem)}

          {/* NOVA DIVIDER: Separa Settings do Perfil */}
          <Divider sx={{ bgcolor: DIVIDER_COLOR, width: "75%", alignSelf: "center", }} />

          {/* Exemplo de Perfil */}
          {renderListItem({ text: "Usuário", icon: <AccountCircleIcon />, path: "/profile" }, true)}
        </Box>
      </Box>
    </Box>
  );
}