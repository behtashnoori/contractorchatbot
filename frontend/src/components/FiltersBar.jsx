import PropTypes from 'prop-types';
import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Button from '@mui/material/Button';
import InputAdornment from '@mui/material/InputAdornment';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import dayjs from 'dayjs';
import jalaliday from 'jalaliday';

dayjs.extend(jalaliday);

const STATUS_OPTIONS = [
  { label: 'همه وضعیت‌ها', value: '' },
  { label: 'تایید شده', value: 'تاييد شده' },
  { label: 'در انتظار', value: 'در انتظار' },
  { label: 'رد شده', value: 'رد شده' },
];

export function FiltersBar({ filters, onChange, onReset }) {
  const handleInput = (name) => (event) => {
    onChange({ ...filters, [name]: event.target.value });
  };

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2.5,
        borderRadius: 2,
        bgcolor: 'white',
        display: 'flex',
        flexWrap: 'wrap',
        gap: 2,
        flexDirection: 'row-reverse',
        alignItems: 'center',
      }}
    >
      <TextField
        label="جستجو بر اساس شماره روکش یا فاکتور..."
        value={filters.search ?? ''}
        onChange={handleInput('search')}
        sx={{
          flex: 1,
          minWidth: { xs: '100%', sm: 280 },
          '& .MuiOutlinedInput-root': {
            bgcolor: '#f5f5f5',
            '& fieldset': {
              borderColor: '#e0e0e0',
            },
            '&:hover fieldset': {
              borderColor: '#bdbdbd',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#2196F3',
            },
          },
        }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
            </InputAdornment>
          ),
        }}
      />
      <TextField
        label="وضعیت"
        select
        value={filters.status ?? ''}
        onChange={handleInput('status')}
        sx={{
          minWidth: { xs: '100%', sm: 180 },
          '& .MuiOutlinedInput-root': {
            bgcolor: '#f5f5f5',
            '& fieldset': {
              borderColor: '#e0e0e0',
            },
            '&:hover fieldset': {
              borderColor: '#bdbdbd',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#2196F3',
            },
          },
        }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <FilterListIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
            </InputAdornment>
          ),
        }}
      >
        {STATUS_OPTIONS.map((option) => (
          <MenuItem key={option.value || 'all'} value={option.value}>
            {option.label}
          </MenuItem>
        ))}
      </TextField>
      <Button
        variant="contained"
        onClick={() => onChange(filters)}
        startIcon={<SearchIcon />}
        fullWidth={{ xs: true, sm: false }}
        sx={{
          bgcolor: '#2196F3',
          '&:hover': {
            bgcolor: '#1976D2',
          },
          px: { xs: 2, sm: 3 },
          py: 1.5,
          borderRadius: 2,
          fontWeight: 'bold',
        }}
      >
        جستجو
      </Button>
    </Paper>
  );
}

FiltersBar.propTypes = {
  filters: PropTypes.shape({
    from_date: PropTypes.string,
    to_date: PropTypes.string,
    status: PropTypes.string,
    search: PropTypes.string,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
  onReset: PropTypes.func.isRequired,
};

