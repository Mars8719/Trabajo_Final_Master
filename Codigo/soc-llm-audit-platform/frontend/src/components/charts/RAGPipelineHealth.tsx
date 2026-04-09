import { Box, Typography, Chip, LinearProgress } from '@mui/material';

interface PipelineStage {
  name: string;
  health: number; // 0-100
  injectionBlocked: number;
  lastCheck: string;
}

const defaultStages: PipelineStage[] = [
  { name: 'Input Sanitizer', health: 98, injectionBlocked: 12, lastCheck: '30s ago' },
  { name: 'PII Scanner', health: 95, injectionBlocked: 0, lastCheck: '30s ago' },
  { name: 'LLM Gateway', health: 92, injectionBlocked: 3, lastCheck: '60s ago' },
  { name: 'RAG Retriever', health: 88, injectionBlocked: 2, lastCheck: '60s ago' },
  { name: 'Output Validator', health: 96, injectionBlocked: 5, lastCheck: '30s ago' },
  { name: 'Ethical Gate', health: 99, injectionBlocked: 1, lastCheck: '60s ago' },
];

function getHealthColor(h: number): string {
  if (h >= 90) return '#66bb6a';
  if (h >= 70) return '#ffa726';
  return '#ef5350';
}

interface Props {
  stages?: PipelineStage[];
}

export default function RAGPipelineHealth({ stages = defaultStages }: Props) {
  return (
    <Box sx={{ py: 1 }}>
      {stages.map((stage) => (
        <Box key={stage.name} sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
          <Typography variant="caption" sx={{ width: 110, fontSize: 10, fontWeight: 600 }}>
            {stage.name}
          </Typography>
          <Box sx={{ flexGrow: 1, mx: 1 }}>
            <LinearProgress
              variant="determinate"
              value={stage.health}
              sx={{
                height: 10,
                borderRadius: 1,
                bgcolor: '#333',
                '& .MuiLinearProgress-bar': {
                  bgcolor: getHealthColor(stage.health),
                  borderRadius: 1,
                },
              }}
            />
          </Box>
          <Typography variant="caption" sx={{ width: 35, fontSize: 10, textAlign: 'right' }}>
            {stage.health}%
          </Typography>
          {stage.injectionBlocked > 0 && (
            <Chip
              label={`${stage.injectionBlocked} blocked`}
              size="small"
              color="error"
              variant="outlined"
              sx={{ ml: 1, fontSize: 9, height: 18 }}
            />
          )}
        </Box>
      ))}
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
        OWASP LLM01 / NIS2 — Salud del pipeline + detección injection
      </Typography>
    </Box>
  );
}
