import { useState } from "react";
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  InputAdornment,
  Divider,
} from "@mui/material";

import { EmailOutlined, LockOutlined } from "@mui/icons-material";
import { Link } from "react-router-dom";

export default function LoginTab() {
  // Cores extraídas da sua paleta antiga para referência:
  const colors = {
    primaryMain: "#a10000ff", // Vermelho principal
    primaryDark: "#650000",   // Vermelho escuro (botão)
    bgPaper: "#111111",       // Fundo escuro
    textPrimary: "#ffffff",   // Texto branco
    textSecondary: "rgba(255, 255, 255, 0.7)", // Texto cinza claro
    divider: "#3c3c3c",
  };

  const [emailFocused, setEmailFocused] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const inputStyle = {
    "& .MuiInputLabel-root": {
      color: colors.textSecondary,
    },
    "& .MuiInputLabel-root.Mui-focused": {
      color: colors.textSecondary,
    },
    "& .MuiOutlinedInput-root": {
      "& fieldset": {
        borderColor: colors.divider,
      },
      "&:hover fieldset": {
        borderColor: colors.primaryMain,
      },
      "&.Mui-focused fieldset": {
        borderColor: colors.primaryMain,
      },
    },
    "& .MuiInputBase-input": {
      color: colors.textPrimary,
    },
  };

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
        background: "transparent",
        color: colors.textPrimary,
      }}
    >
      <Paper
        elevation={8}
        sx={{
          p: 5,
          borderRadius: 3,
          width: "100%",
          maxWidth: 380,
          backgroundColor: colors.bgPaper,
          border: `1px solid ${colors.divider}`,
          backdropFilter: "blur(10px)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <Typography
          variant="h5"
          align="center"
          gutterBottom
          sx={{ color: colors.textPrimary, fontWeight: "bold" }}
        >
          Entrar
        </Typography>
        <Divider
          sx={{
            width: "85%",
            backgroundColor: colors.divider,
            mt: 1,
            mb: 2,
          }}
        />

        {/* Campo de Email */}
        <TextField
          label="Email"
          type="email"
          fullWidth
          margin="normal"
          variant="outlined"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          onFocus={() => setEmailFocused(true)}
          onBlur={() => setEmailFocused(false)}
          sx={inputStyle}
          InputProps={{
            startAdornment:
              emailFocused || email ? (
                <InputAdornment position="start">
                  <EmailOutlined sx={{ color: colors.primaryMain }} />
                </InputAdornment>
              ) : null,
          }}
        />

        {/* Campo de Senha */}
        <TextField
          label="Senha"
          type="password"
          fullWidth
          margin="normal"
          variant="outlined"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onFocus={() => setPasswordFocused(true)}
          onBlur={() => setPasswordFocused(false)}
          sx={inputStyle}
          InputProps={{ 
            startAdornment:
              passwordFocused || password ? (
                <InputAdornment position="start">
                  <LockOutlined sx={{ color: colors.primaryMain }} />
                </InputAdornment>
              ) : null,
          }}
        />
        <Divider
          sx={{
            width: "85%",
            backgroundColor: colors.divider,
            mt: 2,
            mb: 2,
          }}
        />

        {/* Botão Login */}
        <Button
          variant="contained"
          fullWidth
          component={Link}
          to="/Home"
          sx={{
            mt: 1,
            width: "85%",
            backgroundColor: colors.primaryDark,
            "&:hover": { backgroundColor: colors.primaryDark },
            borderRadius: "10px",
            py: 1.2,
          }}
        >
          Login
        </Button>

        {/* Linha de 50% usando o componente Divider nativo */}
        <Divider
          sx={{
            width: "50%",
            backgroundColor: colors.divider,
            mt: 2,
          }}
        />
        
        <Typography
          variant="body2"
          align="center"
          sx={{ mt: 2, color: colors.textSecondary, cursor: "pointer" }}
        >
          Problemas ao logar?
        </Typography>
      </Paper>
    </Box>
  );
}