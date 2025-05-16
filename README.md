# UNOPS Remote Sensing Project

This project consists of a Next.js frontend and a Python backend for remote sensing data analysis.

## Prerequisites

- Node.js (v18 or higher)
- Python (v3.8 or higher)
- npm or yarn package manager

## Project Structure

```
├── frontend (Next.js)
│   ├── app/
│   ├── components/
│   ├── pages/
│   ├── public/
│   ├── styles/
│   └── ...
└── python_backend/
```

## Deployment Instructions

### 1. Frontend Setup (Next.js)

1. Install Node.js dependencies:
```bash
npm install
# or
yarn install
```

2. Build the frontend:
```bash
npm run build
# or
yarn build
```

3. Start the production server:
```bash
npm start
# or
yarn start
```

### 2. Backend Setup (Python)

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- On Windows:
```bash
venv\Scripts\activate
```
- On macOS/Linux:
```bash
source venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Start the Python backend (instructions may vary based on your setup)

### Environment Variables

Make sure to set up the following environment variables:
- Create a `.env` file in the root directory
- Add necessary environment variables (contact the development team for required values)

### Additional Notes

- The frontend will be available at `http://localhost:3000` by default
- Make sure both frontend and backend services are running for full functionality
- For development mode, use `npm run dev` or `yarn dev`

## Troubleshooting

If you encounter any issues during deployment:

1. Ensure all prerequisites are installed with the correct versions
2. Check if all environment variables are properly set
3. Make sure both frontend and backend services are running
4. Check the console/terminal for error messages

## Support

For additional support or questions, please contact the development team. 