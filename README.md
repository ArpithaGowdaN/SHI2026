# FSOC PAT Tracker

## AI-Assisted Virtual Pointing, Acquisition and Tracking Simulator for Free-Space Optical Communication

FSOC PAT Tracker is a virtual simulation and analysis platform for **Free-Space Optical Communication (FSOC) Pointing, Acquisition and Tracking (PAT)**.

The project provides a simulated environment in which a camera attempts to acquire and track a moving optical beacon before transitioning toward fine alignment. It combines virtual target motion, camera geometry, target detection, prediction, pan/tilt control, angle-domain analysis, benchmarking, and visualization.

The system is designed as a modular platform so that simulation, tracking, prediction, control, analytics, and visualization can be developed independently and integrated through common interfaces.

---

## 1. Problem Statement

Free-Space Optical Communication uses a narrow optical beam for high-speed communication between platforms such as satellites and UAVs.

Because the optical beam is narrow, the transmitter and receiver must be accurately aligned.

The PAT process can be represented as:

```text
Target / Beacon
      ↓
Coarse Acquisition
      ↓
Target Detection
      ↓
Pointing / Tracking
      ↓
Prediction
      ↓
Pan / Tilt Correction
      ↓
Fine Alignment
```

A major challenge is maintaining the target inside the camera's field of view while the target or platform is moving and disturbances are present.

The proposed system provides a virtual environment for studying this process before implementation on physical hardware.

---

## 2. Proposed Solution

The FSOC PAT Tracker creates a virtual PAT environment containing:

* A virtual world
* Moving beacon targets
* A virtual camera
* Camera field of view (FOV)
* Target position and motion
* Azimuth and elevation geometry
* Pan/tilt information
* Target range in simulation space
* Target detection and tracking
* Target motion prediction
* Pan/tilt control
* PAT performance analytics
* 3D digital-twin visualization
* Benchmarking and reporting

The complete system is modular and follows a defined processing pipeline.

---

## 3. System Architecture

```text
                    FSOC PAT TRACKER
                           │
                           ▼
                  ┌─────────────────┐
                  │ Virtual Scenario│
                  │  simulation.py  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Beacon Detection│
                  │  tracking.py    │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │    Prediction   │
                  │  predictor.py   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Pan/Tilt       │
                  │  Control        │
                  │  control.py     │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ PAT Analytics   │
                  │  analytics.py   │
                  └────────┬────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
             ┌────────────┐ ┌───────────────┐
             │ Reporting  │ │ 3D Digital    │
             │ reporting  │ │ Twin           │
             │    .py     │ │visualization_3d│
             └─────┬──────┘ └───────┬───────┘
                   │                │
                   └───────┬────────┘
                           ▼
                    ┌────────────┐
                    │    GUI     │
                    │ app.py     │
                    │ gui.py     │
                    └─────┬──────┘
                          ▼
                    FINAL DEMO
```

The project's defined integration pipeline is:

```text
simulation.py
      ↓
tracking.py
      ↓
predictor.py
      ↓
control.py
      ↓
analytics.py
      ↓
reporting.py
      ↓
app.py / gui.py
```

---

## 4. Repository Structure

```text
fsoc_pat_tracker/
│
├── README.md
├── requirements.txt
├── run_gui.bat
├── run_demo.bat
│
├── docs/
│   ├── problem_understanding.md
│   ├── technical_report.md
│   ├── user_manual.md
│   └── novelty_notes.md
│
├── outputs/
│   ├── videos/
│   ├── logs/
│   └── plots/
│
├── datasets/
│   ├── input_videos/
│   └── truth_csv/
│
└── src/
    ├── app.py
    ├── gui.py
    ├── config.py
    ├── interfaces.py
    │
    ├── simulation.py
    ├── tracking.py
    ├── predictor.py
    ├── control.py
    │
    ├── analytics.py
    ├── reporting.py
    ├── benchmark.py
    │
    ├── ai_adaptation.py
    └── visualization_3d.py
```

---

# 5. Module Description

## `src/config.py`

Contains common configuration parameters used throughout the project.

Examples include:

* World dimensions
* Camera resolution
* Camera FOV
* Target parameters
* Simulation parameters
* System thresholds

---

## `src/interfaces.py`

Defines the common data structures exchanged between modules.

Examples:

* `FramePacket`
* Tracking results
* Prediction results
* Control commands
* Analytics results

This provides a common interface between different team members' modules.

---

## `src/simulation.py`

**Owner: Electrical A**

Responsible for the virtual physical environment.

Main functions:

* Generate virtual world
* Generate moving target/beacon
* Generate camera viewport
* Model target motion
* Calculate basic camera-target geometry
* Provide FOV information
* Provide PAT geometry

Supported target motion models include:

* Straight line
* Circular
* Figure-8
* Random
* Spiral
* Sinusoidal

The module also supports both simulation mode and real `.mp4` video input.

---

## `src/tracking.py`

**Owner: EC**

Responsible for target/beacon detection and tracking.

Main functions:

* Detect beacon
* Determine target position
* Track target between frames
* Calculate tracking confidence
* Handle tracking disturbances
* Produce tracking results

---

## `src/predictor.py`

**Owner: Electrical B**

Responsible for predicting future target movement.

Main functions:

* Estimate target motion
* Predict future position
* Support predictive reacquisition
* Provide predicted target information to the control system

---

## `src/control.py`

**Owner: Electrical B**

Responsible for camera pointing/control.

Main functions:

* Calculate pointing error
* Generate pan commands
* Generate tilt commands
* Perform predictive PTZ correction
* Support fine-alignment handover

---

## `src/analytics.py`

**Owner: Electrical A**

Responsible for angle-domain PAT analysis.

Main measurements include:

* Azimuth
* Elevation
* Pan error
* Tilt error
* Range
* FOV status
* Angular tracking error
* Acquisition status
* Fine-alignment condition

---

## `src/reporting.py`

**Owner: CS**

Responsible for converting system results into reports and usable outputs.

Possible outputs include:

* Performance summaries
* Tracking statistics
* Error statistics
* Plots
* CSV results

---

## `src/benchmark.py`

**Owner: CS**

Provides performance comparison and benchmarking using simulation data and input videos.

---

## `src/ai_adaptation.py`

**Owner: CS + EC + Electrical B**

Provides the AI-assisted supervisory/adaptation layer.

It can use information from:

* Tracking
* Prediction
* Control
* System performance

to support adaptive system behaviour.

---

## `src/visualization_3d.py`

**Owner: Electrical A**

Provides the optional 3D digital twin.

Visualization includes:

* Camera
* Target
* Camera heading
* Target direction
* FOV cone
* North/East/South/West orientation
* Camera-target geometry

---

## `src/app.py`

**Owner: CS**

Main application/integration layer.

Connects the individual modules into the complete system.

---

## `src/gui.py`

**Owner: CS**

Provides the graphical user interface.

The GUI can display:

* Camera view
* Target status
* Tracking status
* Azimuth
* Elevation
* Range
* FOV status
* Tracking confidence
* Control information
* 3D visualization

---

# 6. Electrical A Contribution

Electrical A is responsible for the **simulation, geometry, angle analysis, FOV and 3D visualization layer**.

### Files

```text
src/simulation.py
src/analytics.py
src/visualization_3d.py
```

### Main contribution

```text
Virtual World
      ↓
Moving Target
      ↓
Camera
      ↓
FOV
      ↓
PAT Geometry
      ↓
Azimuth / Elevation
      ↓
Range
      ↓
Angle Error
      ↓
Fine Alignment Condition
      ↓
3D Digital Twin
```

---

# 7. Novelty

The project combines multiple layers into a single virtual PAT platform.

### Electrical A

**Angle-domain PAT analysis with 3D digital-twin visualization**

This provides geometric understanding of:

* Target direction
* Camera orientation
* FOV
* Angular error
* Target-camera relationship
* Fine-alignment transition

### EC

**Adaptive disturbance-aware beacon detection with confidence scoring**

### Electrical B

**Predictive reacquisition and fine-alignment handover using target prediction and control**

### CS

**AI-assisted supervisory GUI and benchmark/export system**

### Combined novelty

```text
AI-assisted
      +
Virtual PAT Simulation
      +
Disturbance-aware Tracking
      +
Predictive Control
      +
Angle-domain Analysis
      +
3D Digital Twin
      +
Benchmarking
```

---

# 8. Data Flow

```text
Target Motion
     │
     ▼
simulation.py
     │
     │ FramePacket
     ▼
tracking.py
     │
     │ Tracking Result
     ▼
predictor.py
     │
     │ Predicted Position
     ▼
control.py
     │
     │ Pan/Tilt Command
     ▼
Camera / PAT State
     │
     ▼
analytics.py
     │
     ├──────────────► reporting.py
     │
     └──────────────► visualization_3d.py
                              │
                              ▼
                           app.py
                              │
                              ▼
                           gui.py
```

---

# 9. Input Data

The project supports two main operating modes.

### Simulation Mode

The system generates:

* Virtual world
* Moving beacon
* Camera viewport
* PAT geometry

### Video Mode

The system can read a real `.mp4` video for benchmark/video processing.

Input videos are stored in:

```text
datasets/input_videos/
```

Ground-truth data can be stored in:

```text
datasets/truth_csv/
```

---

# 10. Outputs

Generated results are stored under:

```text
outputs/
│
├── videos/
├── logs/
└── plots/
```

Possible outputs:

* Simulation videos
* Tracking logs
* Angular-error plots
* Target trajectories
* Performance measurements
* Benchmark results

---

# 11. Installation

Clone the repository:

```bash
git clone <repository-url>
cd fsoc_pat_tracker
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 12. Running the Project

## Demo Mode

Run:

```bash
run_demo.bat
```

This starts the simulation/demo pipeline.

## GUI Mode

Run:

```bash
run_gui.bat
```

This starts the graphical interface.

---

# 13. Development Order

The project is developed in dependency order:

```text
1. config.py
       ↓
2. interfaces.py
       ↓
3. simulation.py
       ↓
4. tracking.py
       ↓
5. predictor.py
       ↓
6. control.py
       ↓
7. analytics.py
       ↓
8. reporting.py
       ↓
9. app.py / gui.py
       ↓
10. benchmark.py
       ↓
11. ai_adaptation.py
       ↓
12. visualization_3d.py
```

---

# 14. Team Ownership

| Team         | Main Files                                                                       | Responsibility                            |
| ------------ | -------------------------------------------------------------------------------- | ----------------------------------------- |
| CS           | `config.py`, `interfaces.py`, `app.py`, `gui.py`, `reporting.py`, `benchmark.py` | Integration, GUI, reporting, benchmarking |
| EC           | `tracking.py`                                                                    | Beacon detection and tracking             |
| Electrical A | `simulation.py`, `analytics.py`, `visualization_3d.py`                           | Simulation, geometry, FOV, angles, 3D     |
| Electrical B | `predictor.py`, `control.py`                                                     | Prediction and PTZ control                |
| Shared       | `ai_adaptation.py`                                                               | AI/adaptation layer                       |

The project follows the rule of **one primary owner per file**, with shared integration files controlled by CS.

---

# 15. Project Goal

The goal is to create a modular virtual environment for demonstrating and evaluating the **Pointing, Acquisition and Tracking process of an FSOC system**.

The final system should demonstrate:

```text
Target Generation
       ↓
Target Acquisition
       ↓
Target Tracking
       ↓
Target Prediction
       ↓
Pan/Tilt Correction
       ↓
FOV Maintenance
       ↓
Reacquisition
       ↓
Fine Alignment
       ↓
Performance Analysis
       ↓
3D Visualization
```

---

## 16. Project Status

### Current Development

* [x] Repository structure
* [x] Module ownership
* [x] Common interface design
* [x] Virtual target model
* [x] Virtual world generation
* [x] Camera viewport
* [x] Basic FOV geometry
* [ ] Beacon tracking
*

