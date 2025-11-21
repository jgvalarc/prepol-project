import { useState } from "react";
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  InputAdornment,
} from "@mui/material";

import { EmailOutlined, LockOutlined } from "@mui/icons-material";
import { Link } from "react-router-dom";
import { useTheme } from "@mui/material/styles";

export default function LoginTab() {
  const theme = useTheme();

  const [emailFocused, setEmailFocused] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const inputStyle = {
    "& .MuiInputLabel-root": {
      color: theme.palette.text.secondary,
    },
    "& .MuiInputLabel-root.Mui-focused": {
      color: theme.palette.primary.main,
    },
    "& .MuiOutlinedInput-root": {
      "& fieldset": {
        borderColor: theme.palette.divider,
      },
      "&:hover fieldset": {
        borderColor: theme.palette.primary.main,
      },
      "&.Mui-focused fieldset": {
        borderColor: theme.palette.primary.main,
      },
    },
    "& .MuiInputBase-input": {
      color: theme.palette.text.primary,
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
        color: theme.palette.text.primary,
      }}
    >
      <Paper
        elevation={8}
        sx={{
          p: 5,
          borderRadius: 3,
          width: "100%",
          maxWidth: 380,
          backgroundColor: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
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
          sx={{ color: theme.palette.text.primary, fontWeight: "bold" }}
        >
          Entrar
        </Typography>

        {/* Linha superior */}
        <Box
          sx={{
            width: "85%",
            borderBottom: `1px solid ${theme.palette.divider}`,
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
                  <EmailOutlined sx={{ color: theme.palette.primary.main }} />
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
                  <LockOutlined sx={{ color: theme.palette.primary.main }} />
                </InputAdornment>
              ) : null,
          }}
        />

        {/* Linha inferior */}
        <Box
          sx={{
            width: "85%",
            borderBottom: `1px solid ${theme.palette.divider}`,
            mt: 2,
            mb: 2,
          }}
        />

        {/* Botão Login */}
        <Button
          variant="contained"
          fullWidth
          component={Link}
          to="/Map"
          sx={{
            mt: 1,
            width: "85%",
            backgroundColor: theme.palette.primary.dark,
            "&:hover": { backgroundColor: theme.palette.primary.dark },
            borderRadius: "10px",
            py: 1.2,
          }}
        >
          Login
        </Button>

        <Box
          sx={{
            width: "50%",
            borderBottom: `1px solid ${theme.palette.divider}`,
            mt: 2,
          }}
        />
        <Typography
          variant="body2"
          align="center"
          sx={{ mt: 2, color: theme.palette.text.secondary, cursor: "pointer" }}
        >
          Problemas ao logar?
        </Typography>
      </Paper>
    </Box>
  );
}
