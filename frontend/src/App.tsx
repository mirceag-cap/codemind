// App root — health check page using Material UI

import { useEffect, useState } from 'react'
import {
  Box, Card, CardContent, Chip, CircularProgress,
  CssBaseline, Divider, Stack, ThemeProvider,
  Typography, createTheme, Alert
} from '@mui/material'
import { fetchHealth } from './services/api'

// dark theme — matches the coding assistant vibe
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#7c3aed' },      // purple accent
    background: {
      default: '#0f0f0f',
      paper: '#1a1a1a',
    },
  },
  shape: { borderRadius: 12 },
})

type HealthData = {
  status: string
  app: string
  debug: boolean
  weaviate_url: string
}

export default function App() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((e: Error) => setError(e.message))
  }, [])

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />  {/* MUI's CSS reset — applies dark background globally */}
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: 'background.default',
        }}
      >
        <Card sx={{ width: 420, p: 2, border: '1px solid #2a2a2a' }} elevation={6}>
          <CardContent>
            <Typography variant="h4" fontWeight={700} gutterBottom>
              ⚙️ CodeMind
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={4}>
              Agentic codebase assistant
            </Typography>

            <Typography
              variant="overline"
              color="text.disabled"
              display="block"
              mb={2}
            >
              Backend Status
            </Typography>

            {/* Error state */}
            {error && (
              <Alert severity="error" sx={{ fontSize: 13 }}>
                {error} — is FastAPI running on port 8000?
              </Alert>
            )}

            {/* Loading state */}
            {!health && !error && (
              <Stack direction="row" alignItems="center" gap={2}>
                <CircularProgress size={16} />
                <Typography variant="body2" color="text.secondary">
                  Connecting to backend...
                </Typography>
              </Stack>
            )}

            {/* Success state */}
            {health && (
              <Stack divider={<Divider />} spacing={0}>
                <Row label="Status">
                  <Chip label={health.status} color="success" size="small" />
                </Row>
                <Row label="App">
                  <Typography variant="body2">{health.app}</Typography>
                </Row>
                <Row label="Weaviate">
                  <Typography variant="body2" color="text.secondary">
                    {health.weaviate_url}
                  </Typography>
                </Row>
                <Row label="Debug">
                  <Chip
                    label={health.debug ? 'true' : 'false'}
                    size="small"
                    color={health.debug ? 'warning' : 'default'}
                  />
                </Row>
              </Stack>
            )}
          </CardContent>
        </Card>
      </Box>
    </ThemeProvider>
  )
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <Stack direction="row" justifyContent="space-between" alignItems="center" py={1.5}>
      <Typography variant="body2" color="text.secondary">{label}</Typography>
      {children}
    </Stack>
  )
}