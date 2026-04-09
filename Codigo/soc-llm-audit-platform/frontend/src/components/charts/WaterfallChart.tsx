import { Box, Typography } from '@mui/material';

interface Feature {
  feature: string;
  value: number;
  shap_value: number;
  impact: string;
}

interface Props {
  features: Feature[];
}

export default function WaterfallChart({ features }: Props) {
  const maxVal = Math.max(...features.map((f) => Math.abs(f.shap_value)));
  const barWidth = 280;

  return (
    <Box sx={{ py: 2 }}>
      {features.map((f) => {
        const width = (Math.abs(f.shap_value) / maxVal) * barWidth;
        const isPositive = f.shap_value > 0;
        return (
          <Box key={f.feature} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Typography variant="caption" sx={{ width: 140, textAlign: 'right', mr: 1, fontSize: 11 }}>
              {f.feature.replace(/_/g, ' ')}
            </Typography>
            <Box sx={{ position: 'relative', width: barWidth, height: 20 }}>
              <Box
                sx={{
                  position: 'absolute',
                  left: isPositive ? barWidth / 2 : barWidth / 2 - width,
                  width,
                  height: 20,
                  bgcolor: isPositive ? '#66bb6a' : '#ef5350',
                  borderRadius: 1,
                }}
              />
            </Box>
            <Typography variant="caption" sx={{ ml: 1, fontWeight: 700, fontSize: 11 }}>
              {f.shap_value > 0 ? '+' : ''}{f.shap_value.toFixed(2)}
            </Typography>
          </Box>
        );
      })}
    </Box>
  );
}
