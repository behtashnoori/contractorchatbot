import PropTypes from 'prop-types';
import Chip from '@mui/material/Chip';
import { getStatusVisuals } from '../utils/status.js';

export function StatusChip({ status, size = 'small', sx = {} }) {
  if (!status) {
    return null;
  }

  const visuals = getStatusVisuals(status);
  return (
    <Chip
      label={status}
      size={size}
      sx={{
        fontWeight: 'bold',
        bgcolor: visuals.bgColor,
        color: visuals.color,
        border: `1px solid ${visuals.color}`,
        ...sx,
      }}
    />
  );
}

StatusChip.propTypes = {
  status: PropTypes.string,
  size: PropTypes.oneOf(['small', 'medium']),
  sx: PropTypes.object,
};
