import * as React from 'react';
import { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Divider from '@mui/material/Divider'; 
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Menu from '@mui/material/Menu';
import CircularProgress from '@mui/material/CircularProgress'; 

// Importações para Pickers
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import dayjs from 'dayjs';

// 1. Importação dos Ícones
import HomeIcon from '@mui/icons-material/Home';
import SettingsIcon from '@mui/icons-material/Settings';
import TuneIcon from '@mui/icons-material/Tune'; 

// 🎨 DEFINIÇÕES DE CORES E ESTILOS
const SIDEBAR_BG_COLOR = "#090909"; 
const CURRENT_TEXT_COLOR = "#fff"; 
const DIVIDER_COLOR = "#777777"; 
const MENU_BG_COLOR = "#1e1e1e";       // <-- Fundo Escuro do Menu
const PICKER_BORDER_COLOR = "#4a90e2"; // <-- Borda Azul/Ciano para os Pickers
const MENU_WIDTH = 320; 

// Estilo de Hover (Mantido)
const lineHoverStyle = {
    position: "relative",
    color: CURRENT_TEXT_COLOR, 
    borderRadius: '4px',
    
    "&:hover": {
        backgroundColor: 'rgba(255, 255, 255, 0.05)', 
    },
};

// 🎯 ESTILO PARA OS CAMPOS DE TEXTO (Pickers e Select)
const darkInputStyle = {
    // Cor do texto de entrada e labels
    '& .MuiInputBase-root': {
        color: CURRENT_TEXT_COLOR,
        // Cor e espessura da borda padrão
        '& fieldset': {
            borderColor: PICKER_BORDER_COLOR,
        },
        // Cor e espessura da borda no hover
        '&:hover fieldset': {
            borderColor: PICKER_BORDER_COLOR, 
        },
        // Cor da borda quando o campo está focado/selecionado
        '&.Mui-focused fieldset': {
            borderColor: PICKER_BORDER_COLOR, // Pode ser uma cor mais clara aqui, se desejar
        },
    },
    // Cor da label (rótulo)
    '& .MuiInputLabel-root': {
        color: DIVIDER_COLOR, // Cinza
        '&.Mui-focused': {
            color: PICKER_BORDER_COLOR, // Azul
        },
    },
    // Cor do ícone do calendário/relógio
    '& .MuiSvgIcon-root': {
        color: DIVIDER_COLOR,
    }
};

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// --- CONTEÚDO DO MENU DE PREDIÇÃO (Aplicando Estilos) ---
function PredictionMenuContent({ onClose, onApplyFilters }) {
    // ... (Estados mantidos)
    const [startDate, setStartDate] = useState(null);
    const [endDate, setEndDate] = useState(null);
    const [startTime, setStartTime] = useState(null);
    const [endTime, setEndTime] = useState(null);
    const [model, setModel] = useState('');
    const [error, setError] = useState('');
    const [dateRange, setDateRange] = useState(null);
    const [loadingMetadata, setLoadingMetadata] = useState(true);

    // Fetch available date range from API
    useEffect(() => {
        const fetchMetadata = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/metadata`);
                if (!response.ok) {
                    throw new Error('Failed to fetch metadata');
                }
                const data = await response.json();
                setDateRange(data.date_range);
            } catch (err) {
                console.error('Error fetching metadata:', err);
                setDateRange({ min: 'N/A', max: 'N/A' });
            } finally {
                setLoadingMetadata(false);
            }
        };

        fetchMetadata();
    }, []);

    const handleModelChange = (event) => {
        setModel(event.target.value);
    };

    const handleApply = () => {
        setError('');
        
        // Validate dates
        if (!startDate || !endDate) {
            setError('Por favor, selecione as datas de início e fim');
            return;
        }

        // Format dates for API
        const formattedStart = startDate.format('YYYY-MM-DD');
        const formattedEnd = endDate.format('YYYY-MM-DD');

        // Validate date range
        const daysDiff = endDate.diff(startDate, 'day') + 1;
        if (daysDiff < 1) {
            setError('A data final deve ser posterior à data inicial');
            return;
        }
        if (daysDiff > 31) {
            setError('O intervalo de datas não pode exceder 31 dias');
            return;
        }

        // Validate against available date range
        if (dateRange && dateRange.min && dateRange.max) {
            const availableStart = new Date(dateRange.min);
            const availableEnd = new Date(dateRange.max);
            const selectedStart = startDate.toDate();
            const selectedEnd = endDate.toDate();

            if (selectedStart < availableStart || selectedEnd > availableEnd) {
                setError(`As datas selecionadas devem estar entre ${dateRange.min} e ${dateRange.max}`);
                return;
            }
        }

        // Call parent handler with date range
        onApplyFilters({
            startDate: formattedStart,
            endDate: formattedEnd
        });

        onClose();
    };

    return (
        <LocalizationProvider dateAdapter={AdapterDayjs}>
            <Box 
                sx={{ width: MENU_WIDTH, p: 2, color: CURRENT_TEXT_COLOR }} // Garantindo cor de texto branca
            >
                <Typography variant="h6" gutterBottom align='center'>
                    Controles de Predição
                </Typography>
                <Divider sx={{ mb: 3, bgcolor: DIVIDER_COLOR,}} />

                <Stack spacing={3}>
                    {/* 1. Seleção de Modelos (Select) */}
                    <FormControl fullWidth size="small" sx={darkInputStyle}>
                        <InputLabel>Tipo de crime</InputLabel>
                        <Select
                            value={model}
                            label="Modelo"
                            onChange={handleModelChange}
                        >
                            <MenuItem value="model_a">Crime A </MenuItem>
                            <MenuItem value="model_b">Crime B </MenuItem>
                            <MenuItem value="model_c">Crime C </MenuItem>
                        </Select>
                    </FormControl>
                    
                    {/* 2. Pickers de Data */}
                    <Typography variant="subtitle2" fontWeight="bold">Período</Typography>
                    <DatePicker 
                        format='DD/MM/YYYY'
                        label="Data Inicial"
                        value={startDate}
                        onChange={setStartDate}
                        minDate={dateRange?.min ? dayjs(dateRange.min) : undefined}
                        maxDate={dateRange?.max ? dayjs(dateRange.max) : undefined}
                        slotProps={{ 
                            textField: { 
                                fullWidth: true, 
                                size: "small", 
                                sx: darkInputStyle
                            } 
                        }}
                    />
                    <DatePicker
                        format='DD/MM/YYYY' 
                        label="Data Final"
                        value={endDate}
                        onChange={setEndDate}
                        minDate={dateRange?.min ? dayjs(dateRange.min) : undefined}
                        maxDate={dateRange?.max ? dayjs(dateRange.max) : undefined}
                        slotProps={{ textField: { fullWidth: true, size: "small", sx: darkInputStyle } }}
                    />

                    {/* 3. Pickers de Hora */}
                    {/* Time pickers hidden for now - not used by API
                    <TimePicker 
                        label="Hora Início"
                        value={startTime}
                        onChange={setStartTime}
                        slotProps={{ textField: { fullWidth: true, size: "small", sx: darkInputStyle } }}
                    />
                    <TimePicker 
                        label="Hora Fim"
                        value={endTime}
                        onChange={setEndTime}
                        slotProps={{ textField: { fullWidth: true, size: "small", sx: darkInputStyle } }}
                    />
                    */}

                    {error && (
                        <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                            {error}
                        </Typography>
                    )}
                    
                    <Button variant="contained" onClick={handleApply} sx={{ mt: 2 }}>
                        Aplicar Filtros
                    </Button>
                    
                    {loadingMetadata ? (
                        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
                            <CircularProgress size={16} sx={{ color: '#888' }} />
                        </Box>
                    ) : (
                        <Typography 
                            variant="caption" 
                            sx={{ 
                                mt: 1, 
                                color: error && error.includes('must be between') ? '#f44336' : '#888', 
                                textAlign: 'center', 
                                display: 'block',
                                transition: 'color 0.3s ease'
                            }}
                        >
                            {dateRange ? `Disponível: ${dateRange.min} a ${dateRange.max}` : 'Carregando intervalo de datas...'}
                        </Typography>
                    )}
                </Stack>
            </Box>
        </LocalizationProvider>
    );
}


// --- COMPONENTE PRINCIPAL ---
export default function IconTooltipGroup({ onApplyFilters }) {
    const [anchorEl, setAnchorEl] = useState(null);
    const isMenuOpen = Boolean(anchorEl);

    const handleToggleMenu = (event) => {
        if (isMenuOpen) {
            setAnchorEl(null);
        } else {
            setAnchorEl(event.currentTarget);
        }
    };

    const handleCloseMenu = () => {
        setAnchorEl(null);
    };

    const iconButtonsData = [
        { key: 'home', icon: <HomeIcon />, title: 'Início', action: () => console.log('Navegar para Início') },
        { 
            key: 'prediction', 
            icon: <TuneIcon />, 
            title: 'Controles de Predição', 
            action: handleToggleMenu 
        },
        { key: 'settings', icon: <SettingsIcon />, title: 'Configurações', action: () => console.log('Abrir Configurações') },
    ];

    return (
        <React.Fragment>
            {/* BARRA DE ÍCONES (Mantida) */}
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
                {/* ... (Botões e Divisores mantidos) ... */}
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
                                    id={item.key === 'prediction' ? 'prediction-button' : undefined}
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

            {/* MENU FLUTUANTE DE CONTROLES DE PREDIÇÃO */}
            <Menu
                anchorEl={anchorEl}
                open={isMenuOpen}
                onClose={handleCloseMenu}
                anchorOrigin={{ vertical: 'top', horizontal: 'left' }}
                transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                slotProps={{
                    paper: {
                        sx: {
                            // 🚨 Fundo do Menu Escuro
                            backgroundColor: MENU_BG_COLOR, 
                            boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                            border: '1px solid #333',
                            borderRadius: 2,
                            // Garante que o texto dentro do Menu seja legível
                            color: CURRENT_TEXT_COLOR, 
                            ml: -2,
                            mt: -7,
                        }
                    }
                }}
            >
                <PredictionMenuContent onClose={handleCloseMenu} onApplyFilters={onApplyFilters} />
            </Menu>
        </React.Fragment>
    );
}