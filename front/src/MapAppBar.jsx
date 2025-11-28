import * as React from 'react';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Divider from '@mui/material/Divider'; 
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

// Importações dos Ícones
import HomeIcon from '@mui/icons-material/Home';
import SettingsIcon from '@mui/icons-material/Settings'; 

// 🎨 DEFINIÇÕES DE CORES E ESTILOS
const SIDEBAR_BG_COLOR = "#090909"; 
const CURRENT_TEXT_COLOR = "#fff"; 
const DIVIDER_COLOR = "#777777"; 

// Estilo de Hover (Mantido)
const lineHoverStyle = {
    position: "relative",
    color: CURRENT_TEXT_COLOR, 
    borderRadius: '4px',
    
    "&:hover": {
        backgroundColor: 'rgba(255, 255, 255, 0.05)', 
    },
};


// --- COMPONENTE PRINCIPAL ---
export default function IconTooltipGroup() {
    const iconButtonsData = [
        { key: 'home', icon: <HomeIcon />, title: 'Início', action: () => window.location.href = '/Home' },
        { key: 'settings', icon: <SettingsIcon />, title: 'Configurações', action: () => console.log('Abrir Configurações') },
    ];

    return (
        <React.Fragment>
            {/* BARRA DE ÍCONES SIMPLIFICADA */}
            <Box
                sx={{
                    position: 'fixed',
                    top: 25,
                    right: 10,
                    zIndex: 1000,
                    padding: 1,
                    borderRadius: 2,
                    backgroundColor: SIDEBAR_BG_COLOR,
                    boxShadow: '0 4px 8px rgba(0, 0, 0, 0.5)',
                }}
            >
                <Stack direction="column" spacing={0.5}> 
                    {iconButtonsData.map((item, index) => (
                        <React.Fragment key={item.key}>
                            <Tooltip 
                                title={item.title} 
                                placement="left"
                            >
                                <IconButton
                                    disableRipple 
                                    onClick={item.action} 
                                    size="large"
                                    sx={{ 
                                        ...lineHoverStyle,
                                        backgroundColor: 'transparent',
                                        width: '40px', 
                                        height: '40px',
                                        padding: 0, 
                                        display: 'flex',
                                        justifyContent: 'center',
                                        alignItems: 'center',
                                    }}
                                >
                                    {item.icon}
                                </IconButton>
                            </Tooltip>
                            
                            {index < iconButtonsData.length - 1 && (
                                <Divider 
                                    sx={{ 
                                        my: 0.5, 
                                        width: '70%', 
                                        mx: 'auto', 
                                        bgcolor: DIVIDER_COLOR,
                                        height: '1px', 
                                        border: 'none',
                                        alignSelf: 'center',
                                    }} 
                                />
                            )}
                        </React.Fragment>
                    ))}
                </Stack>
            </Box>
        </React.Fragment>
    );
}