// Start both local servers. Ctrl+C stops both; requires .venv and npm install.
import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

process.chdir(fileURLToPath(new URL('..', import.meta.url)))
const python = process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python'
if (!existsSync(python)) {
  console.error('Create the virtual environment first. See README.md → Local development.')
  process.exit(1)
}
const children = []
let stopping = false
function stop(code = 0) {
  if (stopping) return
  stopping = true
  for (const child of children) child.kill('SIGTERM')
  process.exitCode = code
}
for (const [command, args] of [
  [python, ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8000']],
  [process.execPath, ['node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', '5173', '--strictPort']],
]) {
  const child = spawn(command, args, { stdio: 'inherit', env: process.env })
  children.push(child)
  child.on('error', error => { console.error(error.message); stop(1) })
  child.on('exit', code => { if (!stopping) stop(code ?? 1) })
}
process.on('SIGINT', () => stop())
process.on('SIGTERM', () => stop())
