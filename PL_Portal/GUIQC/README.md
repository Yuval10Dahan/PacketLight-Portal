# ALM Dashboard - Quality Center Execution Progress

A modern web dashboard for visualizing and tracking test execution progress in **Micro Focus ALM (Quality Center)**. Built with Python FastAPI backend and React frontend.

## 🌟 Features

- **Real-time Dashboard**: View test execution progress with interactive donut charts
- **Drill-Down Navigation**: Navigate through folder hierarchy from high-level overview to individual tests
- **Beautiful UI**: Modern, responsive design with Tailwind CSS and premium aesthetics
- **Smart Aggregation**: Automatically aggregates test statistics (Executed vs. Not Executed)
- **Test Table View**: Sortable table at leaf level showing individual test details

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **FastAPI** for high-performance async API
- **ALM REST API Integration** with session management
- **Data Aggregation** logic for folder-based statistics
- **CORS** enabled for frontend communication

### Frontend (React/Vite)
- **React 18** with modern hooks
- **Vite** for blazing-fast development
- **Tailwind CSS** for styling
- **Recharts** for data visualization
- **React Query** for efficient data fetching
- **Lucide React** for beautiful icons

## 📋 Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- **Access to ALM/Quality Center** with valid credentials

## 🚀 Installation & Setup

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Copy .env.example to .env and fill in your ALM credentials
copy .env.example .env
```

**Edit `.env` file:**
```env
ALM_BASE_URL=https://your-alm-server.com
ALM_DOMAIN=YOUR_DOMAIN
ALM_PROJECT=YOUR_PROJECT
ALM_USER=your_username
ALM_PASSWORD=your_password
ROOT_FOLDER_ID=110
```

**Run the backend:**
```bash
# From backend directory
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The dashboard will be available at `http://localhost:5173`

## 📁 Project Structure

```
QC/
├── backend/
│   ├── alm_client.py      # ALM API integration & data logic
│   ├── main.py            # FastAPI application
│   ├── requirements.txt   # Python dependencies
│   └── .env.example       # Environment template
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Dashboard.jsx   # Main dashboard with charts
    │   │   └── TestTable.jsx   # Test list table
    │   ├── App.jsx        # Main app component
    │   ├── main.jsx       # Entry point
    │   ├── api.js         # API service layer
    │   └── index.css      # Global styles
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── tailwind.config.js
```

## 🎯 Usage

1. **Start Backend**: Run the FastAPI server (port 8000)
2. **Start Frontend**: Run the Vite dev server (port 5173)
3. **Open Browser**: Navigate to `http://localhost:5173`
4. **Explore**: 
   - View overall execution progress on the home screen
   - Click on sub-folders to drill down
   - Use breadcrumbs to navigate back up
   - At the leaf level, view detailed test table

## 🔧 API Endpoints

- `GET /` - Health check
- `GET /api/config` - Get initial configuration (root folder ID)
- `GET /api/dashboard/stats/{folder_id}` - Get statistics for a specific folder

## 🎨 Design Highlights

- **Glassmorphism** effects on header
- **Color-coded status badges** (Passed, Failed, Blocked, etc.)
- **Smooth animations** and hover effects
- **Responsive grid layouts**
- **Interactive charts** with Recharts
- **Clean typography** with Inter font

## 🐛 Troubleshooting

### Backend Issues

- **Authentication fails**: Verify ALM credentials in `.env`
- **Connection errors**: Check ALM_BASE_URL and network connectivity
- **Module not found**: Ensure all dependencies are installed (`pip install -r requirements.txt`)

### Frontend Issues

- **Blank page**: Check browser console for errors
- **API errors**: Ensure backend is running on port 8000
- **Build errors**: Delete `node_modules` and run `npm install` again

## 📝 Notes

- The dashboard uses the ALM REST API cross-filter syntax for efficient queries
- Session cookies are managed automatically by the `ALMClient` class
- For production deployment, update CORS settings in `backend/main.py`
- Large datasets may require pagination (currently set to 2000 items per request)

## 🤝 Contributing

This project was generated as a full-stack implementation for ALM Quality Center integration. Feel free to extend it with:
- Additional chart types
- Export functionality (PDF/Excel)
- Advanced filters
- Test execution triggers

## 📄 License

Internal use - PacketLight Networks

## 👨‍💻 Author

Generated for PacketLight Networks Quality Team
