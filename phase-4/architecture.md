graph TD
    %% Client Layer
    Client[Client / Swagger UI / Browser] -->|HTTP GET / POST| FastAPI[FastAPI Application / app/main.py]

    %% Routing & Business Logic Layer
    subgraph FastAPI Backend
        FastAPI --> Routers[API Routers / app/routers]
        Routers -->|Payroll Exports| ExportModule[exports.py / Pandas DataFrames]
        Routers -->|Data Seeding| SeedModule[seed.py / CSV Processors]
    end

    %% Data & Persistence Layer
    subgraph Data Layer
        ExportModule -->|SQLAlchemy Text Queries / db.bind| SQLite[(SQLite Database / ledger.db)]
        SeedModule -->|Drop & Create / Bulk Insert| SQLite
        SQLite -->|Persistent Records & Custom Trials| ExportModule
    end

    %% Response
    ExportModule -->|Streaming CSV Response| Client