import { Box, Typography, GlobalStyles, } from "@mui/material";
import LoginTab from './LoginTab.jsx'
import Logo from './assets/Logo.png'
import PixelBlast from './Components/PixelBlast.jsx';

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

      <Box>
        <Box
        sx={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
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
          zIndex: 0,
        }}
      >
        <PixelBlast />
      </Box>
        <LoginTab/>
        <Box
          sx={{
            position: "absolute",
            top: 24,
            left: 32,
            display: "flex",
            alignItems: "center",
          }}
        >
          <Box
            component="img"
            src={Logo}
            alt="Logo"
            sx={{
              height: 48,
              width: 48,
              mr: 0.5,
            }}
          />

          <Typography
            variant="h5"
            sx={{
              fontWeight: "bold",
              color: "#ffffffff",
              letterSpacing: 1.5,
              fontFamily: "Poppins, sans-serif",
            }}
          >
            PREPOL
          </Typography>
        </Box>
      </Box>
    </>
  );
}
