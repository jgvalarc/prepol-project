import { Box, Typography, GlobalStyles, ThemeProvider } from "@mui/material";
import LoginTab from './LoginTab.jsx'
import Palette from "./Palette.jsx"

export default function BackgroundPage() {
  return (
    <>
      <GlobalStyles
        styles={{
          "html, body, #root": {
            margin: 0,
            padding: 0,
            width: "100%",
            height: "100%",
            overflow: "hidden",
          },
        }}
      />

      <Box
        sx={{
          width: "100%",
          height: "100vh",
          backgroundColor: "#0a0a0a",
          backgroundImage: `
            repeating-linear-gradient(
              45deg,
              rgba(80, 80, 80, 0.1) 0px,
              rgba(43, 43, 43, 0.1) 1px,
              transparent 1px,
              transparent 20px
            )
          `,
          position: "relative",
        }}
      >
        <ThemeProvider theme={Palette}>
        <LoginTab/>
        </ThemeProvider>
        <Typography
          variant="h5"
          sx={{
            position: "absolute",
            top: 24,
            left: 32,
            fontWeight: "bold",
            color: "#ffffffff",
            letterSpacing: 1.5,
            fontFamily: "Poppins, sans-serif",
          }}
        >
          PREPOL
        </Typography>
      </Box>
    </>
  );
}
