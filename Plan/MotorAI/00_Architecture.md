# 🏗️ Motor AI Solution - 기술 아키텍처

---

## 1. 전체 시스템 아키텍처

```mermaid
graph TD
    subgraph DataLayer["🗄️ Data Layer"]
        MC["Motor-CAD .txt"] -->|자체 파서| H5[(.h5 Dataset)]
        AX["Ansys Maxwell"] -->|변환| H5
        H5 -->|Training| FNO["PhysicsNemo FNO"]
        H5 -->|Viz| ADP["VTK Adapter\nPyVista"]
    end

    subgraph AILayer["🧠 AI Compute Layer (GPU)"]
        FNO --> MDL["Trained Model\ncheckpoint.pt"]
        WARP["NVIDIA Warp\nGPU Kernel"] <-->|Differentiable| MDL
    end

    subgraph BackendLayer["⚙️ Backend - FastAPI"]
        MDL -->|Inference| API["FastAPI Server"]
        WARP -->|Physics Calc| API
        ADP -->|Binary| API
    end

    subgraph FrontendLayer["🖥️ Frontend - Browser"]
        API -->|Float32Array| TS["TypeScript / React"]
        TS --> BJX["Babylon.js 3D"]
        BJX --> SHD["GLSL Shaders\nContour/ColorMap"]
        BJX --> WASM["WebAssembly\nC++/Rust"]
    end

    subgraph ProtoLayer["🚀 Phase 1 Prototype"]
        ADP --> STL["Streamlit App"]
        STL --> STPV["stpyvista Widget"]
    end

    style DataLayer fill:#1a1a2e,color:#eee
    style AILayer fill:#16213e,color:#eee
    style BackendLayer fill:#0f3460,color:#eee
    style FrontendLayer fill:#533483,color:#eee
    style ProtoLayer fill:#2d6a4f,color:#eee
```

---

## 2. 데이터 파이프라인 플로우

```mermaid
flowchart LR
    A["🔧 Motor-CAD .txt"] -->|파서| B["📦 .h5 Dataset"]
    B --> C{용도}
    C -->|학습| D["🧠 FNO Training\nPhysicsNemo"]
    C -->|시각화| E["🔬 VTK Adapter\nPyVista"]
    D --> F["💾 Model\nCheckpoint"]
    E --> G["📁 .vtu File"]
    G --> H["🖥️ ParaView\n검증"]
    G --> I["🌐 Streamlit\nPhase 1"]
    F --> J["⚡ FastAPI\nInference"]
    J -->|Float32Array| K["🎮 Babylon.js"]
    K --> L["✨ GLSL Shaders\n실시간 컬러맵"]
```

---

## 3. 기술 학습 의존성 맵

```mermaid
graph LR
    A["Python ✅ 완료"] --> B["PyVista/VTK\n📅 Month 1"]
    A --> C["FastAPI\n📅 Month 4"]
    B --> D["stpyvista\n📅 Month 2"]
    D --> E["Streamlit App\n📅 Month 2"]
    F["TypeScript\n📅 Month 3"] --> G["Babylon.js\n📅 Month 3"]
    G --> H["GLSL Shaders\n📅 Month 5"]
    H --> I["Custom Contour\n📅 Month 6"]
    C --> J["Binary Stream\n📅 Month 4"]
    J --> G
    K["NVIDIA Warp\n📅 Month 7"] --> L["GPU Kernel\n📅 Month 7"]
    L --> M["Differentiable\nPhysics Month 9"]
    N["C++ 기초\n📅 Month 10"] --> O["WebAssembly\n📅 Month 10"]
    O --> P["WebGPU\n📅 Month 11"]

    style A fill:#2d6a4f,color:#fff
    style B fill:#1b4332,color:#fff
    style F fill:#1a1a2e,color:#fff
    style K fill:#16213e,color:#fff
    style N fill:#0f3460,color:#fff
```

---

## 4. 1년 개발 타임라인

```mermaid
gantt
    title 🚀 Motor AI Solution - 1년 로드맵 (2026-2027)
    dateFormat YYYY-MM-DD
    axisFormat %m월

    section Phase 1 기반 구축
    M1 데이터 어댑터 h5→VTK    :a1, 2026-04-01, 30d
    M2 Streamlit 3D 대시보드    :a2, after a1, 30d
    M3 Babylon.js 입문          :a3, after a2, 30d

    section Phase 2 고성능 시각화
    M4 FastAPI 바이너리 스트리밍 :b1, 2026-07-01, 30d
    M5 GLSL Shader 컬러맵        :b2, after b1, 30d
    M6 인터랙티브 UI             :b3, after b2, 30d

    section Phase 3 솔버 & AI 통합
    M7 NVIDIA Warp GPU 커널      :c1, 2026-10-01, 30d
    M8 FNO 추론 서버 연동         :c2, after c1, 30d
    M9 미분가능 시뮬레이션        :c3, after c2, 30d

    section Phase 4 최적화
    M10 WebAssembly 적용         :d1, 2027-01-01, 30d
    M11 WebGPU 전환              :d2, after d1, 30d
    M12 Docker 배포 & IP 문서화  :d3, after d2, 30d
```

---

## 5. 3계층 시스템 구조 요약

```
┌─────────────────────────────────────────┐
│  🧠 SERVER-SIDE (The Brain)             │
│  NVIDIA Warp + PhysicsNemo/FNO         │
│  PyTorch · Python · GPU 환경           │
├─────────────────────────────────────────┤
│  ⚙️  MIDDLEWARE (The Bridge)            │
│  FastAPI → Float32Array Binary Stream  │
├─────────────────────────────────────────┤
│  🖥️  CLIENT-SIDE (The Interface)        │
│  TypeScript → Babylon.js               │
│  GLSL Shaders (실시간 컬러맵)           │
│  WebAssembly (지오메트리 연산 가속)      │
└─────────────────────────────────────────┘
```
