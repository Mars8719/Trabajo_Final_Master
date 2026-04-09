import { Box, Typography, Tooltip } from '@mui/material';

interface RiskItem {
  label: string;
  impact: number;    // 0-4 (col index: 0=Muy Bajo, 4=Muy Alto)
  likelihood: number; // 0-4 (row index: 0=Muy Alta, 4=Muy Baja)
  color?: string;
}

interface RiskMatrixProps {
  data?: RiskItem[];
  onCellClick?: (item: RiskItem) => void;
}

const DEFAULT_RISKS: RiskItem[] = [
  { label: 'Prompt injection', impact: 4, likelihood: 0, color: '#ef5350' },
  { label: 'Bias no detectado', impact: 3, likelihood: 0, color: '#ef5350' },
  { label: 'Shadow AI', impact: 3, likelihood: 1, color: '#ef5350' },
  { label: 'Drift modelo', impact: 2, likelihood: 1, color: '#ffa726' },
  { label: 'Falta HITL', impact: 2, likelihood: 2, color: '#ffa726' },
  { label: 'PII menor', impact: 1, likelihood: 2, color: '#ffee58' },
  { label: 'Latencia', impact: 1, likelihood: 3, color: '#ffee58' },
  { label: 'Log incompleto', impact: 0, likelihood: 3, color: '#66bb6a' },
  { label: 'Config menor', impact: 0, likelihood: 4, color: '#66bb6a' },
];

const impactLabels = ['Muy Bajo', 'Bajo', 'Medio', 'Alto', 'Muy Alto'];
const likelihoodLabels = ['Muy Alta', 'Alta', 'Media', 'Baja', 'Muy Baja'];

function buildMatrix(items: RiskItem[]) {
  const grid: (RiskItem | null)[][] = Array.from({ length: 5 }, () => Array(5).fill(null));
  for (const item of items) {
    const r = Math.max(0, Math.min(4, item.likelihood));
    const c = Math.max(0, Math.min(4, item.impact));
    if (!grid[r][c]) grid[r][c] = item;
  }
  return grid;
}

function cellColor(row: number, col: number): string {
  const severity = row + col; // 0-8 inverted: lower row = higher likelihood
  const idx = (4 - row) + col;  // 0=low risk, 8=high risk
  if (idx >= 6) return '#ef5350';
  if (idx >= 4) return '#ffa726';
  if (idx >= 2) return '#ffee58';
  return '#66bb6a';
}

export default function RiskMatrix({ data, onCellClick }: RiskMatrixProps = {}) {
  const items = data && data.length > 0 ? data : DEFAULT_RISKS;
  const matrix = buildMatrix(items);

  return (
    <Box>
      <Box sx={{ display: 'flex' }}>
        <Box sx={{ width: 60, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', pr: 1 }}>
          {likelihoodLabels.map((l) => (
            <Typography key={l} variant="caption" sx={{ fontSize: 9, textAlign: 'right', height: 44, lineHeight: '44px' }}>
              {l}
            </Typography>
          ))}
        </Box>
        <Box>
          {matrix.map((row, ri) => (
            <Box key={ri} sx={{ display: 'flex', gap: 0.5, mb: 0.5 }}>
              {row.map((cell, ci) => {
                const bg = cell ? (cell.color ?? cellColor(ri, ci)) : '#222';
                return (
                  <Tooltip key={ci} title={cell ? `${cell.label} (Impacto: ${impactLabels[ci]}, Prob: ${likelihoodLabels[ri]})` : ''} arrow>
                    <Box
                      onClick={() => cell && onCellClick?.(cell)}
                      sx={{
                        width: 80, height: 40,
                        bgcolor: cell ? bg + '33' : '#222',
                        border: cell ? `1px solid ${bg}` : '1px solid #333',
                        borderRadius: 1,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        cursor: cell && onCellClick ? 'pointer' : 'default',
                        '&:hover': cell ? { bgcolor: bg + '55' } : {},
                      }}
                    >
                      {cell && (
                        <Typography variant="caption" sx={{ fontSize: 8, textAlign: 'center', px: 0.5 }}>
                          {cell.label}
                        </Typography>
                      )}
                    </Box>
                  </Tooltip>
                );
              })}
            </Box>
          ))}
          <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
            {impactLabels.map((l) => (
              <Typography key={l} variant="caption" sx={{ width: 80, textAlign: 'center', fontSize: 9 }}>
                {l}
              </Typography>
            ))}
          </Box>
        </Box>
      </Box>
      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
        Eje X: Impacto | Eje Y: Probabilidad
      </Typography>
    </Box>
  );
}
