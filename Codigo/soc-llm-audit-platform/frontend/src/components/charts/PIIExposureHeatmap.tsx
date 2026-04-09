import { Box, Typography } from '@mui/material';

interface Cell {
  field: string;
  source: string;
  exposure: number; // 0-100
}

const defaultData: Cell[] = [
  { field: 'Email', source: 'SIEM', exposure: 45 },
  { field: 'Email', source: 'EDR', exposure: 20 },
  { field: 'Email', source: 'NDR', exposure: 10 },
  { field: 'Email', source: 'IAM', exposure: 60 },
  { field: 'IP', source: 'SIEM', exposure: 72 },
  { field: 'IP', source: 'EDR', exposure: 55 },
  { field: 'IP', source: 'NDR', exposure: 85 },
  { field: 'IP', source: 'IAM', exposure: 15 },
  { field: 'DNI/NIE', source: 'SIEM', exposure: 5 },
  { field: 'DNI/NIE', source: 'EDR', exposure: 0 },
  { field: 'DNI/NIE', source: 'NDR', exposure: 0 },
  { field: 'DNI/NIE', source: 'IAM', exposure: 30 },
  { field: 'Phone', source: 'SIEM', exposure: 18 },
  { field: 'Phone', source: 'EDR', exposure: 8 },
  { field: 'Phone', source: 'NDR', exposure: 5 },
  { field: 'Phone', source: 'IAM', exposure: 25 },
  { field: 'IBAN', source: 'SIEM', exposure: 3 },
  { field: 'IBAN', source: 'EDR', exposure: 0 },
  { field: 'IBAN', source: 'NDR', exposure: 0 },
  { field: 'IBAN', source: 'IAM', exposure: 12 },
  { field: 'Name', source: 'SIEM', exposure: 35 },
  { field: 'Name', source: 'EDR', exposure: 15 },
  { field: 'Name', source: 'NDR', exposure: 8 },
  { field: 'Name', source: 'IAM', exposure: 50 },
];

const fields = ['Email', 'IP', 'DNI/NIE', 'Phone', 'IBAN', 'Name'];
const sources = ['SIEM', 'EDR', 'NDR', 'IAM'];

function getHeatColor(exposure: number): string {
  if (exposure >= 70) return '#ef535099';
  if (exposure >= 40) return '#ffa72699';
  if (exposure >= 15) return '#ffee5866';
  if (exposure > 0) return '#66bb6a44';
  return '#222';
}

interface Props {
  data?: Cell[];
}

export default function PIIExposureHeatmap({ data = defaultData }: Props) {
  const getValue = (field: string, source: string) =>
    data.find((d) => d.field === field && d.source === source)?.exposure ?? 0;

  return (
    <Box sx={{ py: 1 }}>
      <Box sx={{ display: 'flex' }}>
        <Box sx={{ width: 55 }} />
        {sources.map((s) => (
          <Typography key={s} variant="caption" sx={{ width: 60, textAlign: 'center', fontSize: 9, fontWeight: 600 }}>
            {s}
          </Typography>
        ))}
      </Box>
      {fields.map((field) => (
        <Box key={field} sx={{ display: 'flex', mb: 0.5 }}>
          <Typography variant="caption" sx={{ width: 55, textAlign: 'right', pr: 1, fontSize: 9, lineHeight: '28px' }}>
            {field}
          </Typography>
          {sources.map((source) => {
            const val = getValue(field, source);
            return (
              <Box
                key={source}
                sx={{
                  width: 56,
                  height: 28,
                  mx: '2px',
                  bgcolor: getHeatColor(val),
                  borderRadius: 0.5,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '1px solid #333',
                }}
              >
                <Typography variant="caption" sx={{ fontSize: 9, fontWeight: val > 0 ? 600 : 400 }}>
                  {val > 0 ? val : '—'}
                </Typography>
              </Box>
            );
          })}
        </Box>
      ))}
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
        GDPR Art.5/32 — Mapa calor exposición PII por campo y fuente
      </Typography>
    </Box>
  );
}
