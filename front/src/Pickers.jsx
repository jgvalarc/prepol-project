import { useState } from "react";
import { Box, MenuItem, Select, InputLabel, FormControl } from "@mui/material";

import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { TimePicker } from "@mui/x-date-pickers/TimePicker";
import { PickersDay } from "@mui/x-date-pickers/PickersDay";
import { styled } from "@mui/material/styles";
import IconButton from "@mui/material/IconButton";
import EditCalendarRoundedIcon from "@mui/icons-material/EditCalendarRounded";
import dayjs from "dayjs";


// Botão customizado igual documentação
const StyledButton = styled(IconButton)(({ theme }) => ({
  borderRadius: theme.shape.borderRadius,
}));

// Dias do calendário com números brancos
const StyledDay = styled(PickersDay)(({ theme }) => ({
  borderRadius: theme.shape.borderRadius,
  color: "#fff",
  "&.Mui-selected": {
    backgroundColor: theme.palette.secondary.main,
    color: "#fff",
  },
  "&.Mui-selected:hover": {
    backgroundColor: theme.palette.secondary.dark,
    color: "#fff",
  },
  "&:hover": {
    backgroundColor: theme.palette.action.hover,
    color: "#fff",
  },
}));

export default function StyledPickers() {
  const [time1, setTime1] = useState(null);
  const [time2, setTime2] = useState(null);
  const [date1, setDate1] = useState(dayjs());
  const [date2, setDate2] = useState(dayjs());
  const [option, setOption] = useState("");

  // Estilo do TextField para todos os pickers
  const pickerTextFieldStyle = {
    variant: "filled",
    color: "secondary",
    slots: {},
    sx: {
      "& .MuiOutlinedInput-root": {
        "& fieldset": { borderColor: "#d0d0d0" },
        "&:hover fieldset": { borderColor: "#bdbdbd" },
        "&.Mui-focused fieldset": { borderColor: "#64b5f6" },
      },
      "& .MuiInputLabel-root": { color: "#888" },
      "& .MuiInputLabel-root.Mui-focused": { color: "#64b5f6" },
      "& .MuiOutlinedInput-input": { color: "#222" },
    },
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3, width: "100%" }}>
        {/* TimePickers estilizados */}
        <TimePicker
          label="Horário inicial"
          value={time1}
          onChange={setTime1}
          slots={{ openPickerButton: StyledButton, openPickerIcon: EditCalendarRoundedIcon }}
          slotProps={{
            openPickerButton: { color: "secondary" },
            textField: pickerTextFieldStyle,
          }}
        />

        <TimePicker
          label="Horário final"
          value={time2}
          onChange={setTime2}
          slots={{ openPickerButton: StyledButton, openPickerIcon: EditCalendarRoundedIcon }}
          slotProps={{
            openPickerButton: { color: "secondary" },
            textField: pickerTextFieldStyle,
          }}
        />

        {/* DatePickers estilizados */}
        <DatePicker
          label="Data inicial"
          value={date1}
          onChange={setDate1}
          slots={{ day: StyledDay, openPickerButton: StyledButton, openPickerIcon: EditCalendarRoundedIcon }}
          slotProps={{
            openPickerButton: { color: "secondary" },
            textField: pickerTextFieldStyle,
          }}
        />

        <DatePicker
          label="Data final"
          value={date2}
          onChange={setDate2}
          slots={{ day: StyledDay, openPickerButton: StyledButton, openPickerIcon: EditCalendarRoundedIcon }}
          slotProps={{
            openPickerButton: { color: "secondary" },
            textField: pickerTextFieldStyle,
          }}
        />

        {/* Select estilizado para combinar */}
        <FormControl fullWidth>
          <InputLabel id="custom-select-label">Opção</InputLabel>
          <Select
            labelId="custom-select-label"
            value={option}
            onChange={(e) => setOption(e.target.value)}
            sx={{
              "& .MuiOutlinedInput-notchedOutline": { borderColor: "#d0d0d0" },
              "&:hover .MuiOutlinedInput-notchedOutline": { borderColor: "#bdbdbd" },
              "&.Mui-focused .MuiOutlinedInput-notchedOutline": { borderColor: "#64b5f6" },
              "& .MuiInputLabel-root": { color: "#888" },
              "& .MuiInputLabel-root.Mui-focused": { color: "#64b5f6" },
              "& .MuiSelect-select": { color: "#222" },
            }}
          >
            <MenuItem value="manha">Manhã</MenuItem>
            <MenuItem value="tarde">Tarde</MenuItem>
            <MenuItem value="noite">Noite</MenuItem>
          </Select>
        </FormControl>
      </Box>
    </LocalizationProvider>
  );
}
