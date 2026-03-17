## Parameter Sweep Coverage and Rationale

This document cross-references all sweep parameters in `param_sweep_config.yaml` with the actual node parameter dumps recorded by `ros2_single_node_replayer`. For each node, it lists:

- **Swept parameters**: present in the node’s params and used as sweep axes.
- **Other notable parameters**: present but *not* swept, with a brief explanation of why they are less relevant for this latency-focused experiment.

Latency is the primary metric; we favor parameters that:

- Directly scale computational work (e.g., horizon length, sampling density, grid resolution, queue sizes, loop frequencies).
- Toggle clearly heavier sub-modules (e.g., additional filters or optimizers).

We **exclude** parameters that primarily affect:

- Diagnostic thresholds or logging.
- Safety/comfort semantics (e.g., jerk limits, behavior thresholds) without clear, monotonic CPU impact on this fixed bag.
- Model paths or options that aren’t valid in your current build.

---

### `ndt_scan_matcher` (`autoware_ndt_scan_matcher_node`)

**Swept (present in params)** – from `/localization/pose_estimator/ndt_scan_matcher.ros__parameters`:

- `ndt.resolution`
- `ndt.max_iterations`
- `ndt.num_threads`
- `ndt.step_size`
- `ndt.trans_epsilon`
- `initial_pose_estimation.particles_num`
- `dynamic_map_loading.map_radius`
- `dynamic_map_loading.lidar_radius`

These control search resolution, convergence criteria, threading, and dynamic map loading radius – all direct cost drivers.

**Other notable params (not swept)**:

- `covariance.covariance_estimation.*`, `score_estimation.*`: covariance / quality modeling; important for estimation quality but only second-order for raw CPU time.
- `sensor_points.required_distance`, `sensor_points.timeout_sec`: data availability policy; with a fixed bag these mostly determine if updates happen, not per-update cost.
- `validation.*`: tolerances and skipping behavior; primarily diagnostic/robustness knobs.

Rationale: swept set already spans the main algorithmic levers; remaining parameters mainly tune quality/robustness, not complexity.

---

### `ekf_localizer` (`autoware_ekf_localizer_node`)

**Swept (present)** – from `/localization/pose_twist_fusion_filter/ekf_localizer.ros__parameters`:

- `node.predict_frequency`
- `node.tf_rate`
- `node.extend_state_step`
- `pose_measurement.pose_smoothing_steps`
- `twist_measurement.twist_smoothing_steps`

These directly control update frequency and history lengths, which dominate EKF workload.

**Other notable params (not swept)**:

- `process_noise.proc_stddev_*`, `simple_1d_filter_parameters.*`: noise covariance and 1D filter tuning – numerically important but small impact on FLOPs.
- `diagnostics.*`, `misc.*` (frame ids, thresholds): diagnostic/output behavior, not main CPU cost.

Rationale: for an EKF, changing frequencies and smoothing windows is the clearest way to change runtime; other parameters mostly affect estimation behavior.

---

### `euclidean_cluster` (`euclidean_cluster_node`)

**Swept (present)**:

- `tolerance`
- `max_cluster_size`
- `min_cluster_size`

These drive neighbor search radius and cluster sizes – the core determinants of clustering cost.

**Other params**:

- Remaining config is mostly topic names, frame ids, and QoS in the Autoware param file.

Rationale: clustering complexity is already well-covered by the chosen three; additional params do not significantly change algorithmic structure.

---

### `occupancy_grid_map_node` (`pointcloud_based_occupancy_grid_map_node`)

**Swept (present)** – from `/perception/occupancy_grid_map/occupancy_grid_map_node.ros__parameters`:

- `map_resolution`
- `map_length`

These determine grid cell size and map extent, and thus the number of cells updated per scan.

**Other notable params (not swept)**:

- `height_filter.{min_height,max_height,use_height_filter}`: filter thresholds; change which points are considered but less directly the per-cell workload.
- `probability_matrix.*`: transition probabilities for occupancy; affect estimation behavior rather than loop count.
- `processing_time_*_tolerance_ms`, `publish_processing_time_detail`: diagnostics only.

Rationale: grid size is the dominant performance knob; additional thresholds are better suited to accuracy studies.

---

### `multi_object_tracker` (`multi_object_tracker_node`)

**Swept (present)**:

- `publish_rate`
- `tracker_lifetime`
- `enable_delay_compensation`

These affect how often tracking runs and how long tracks live, clearly impacting workload.

**Other notable params (not swept)** – from `/perception/object_recognition/tracking/multi_object_tracker.ros__parameters`:

- Large matrices: `can_assign_matrix`, `max_area_matrix` – define which labels/areas are compatible; semantic configuration vs. CPU knobs.
- `input/detection*/channel` / `input_channels.*`: routing/semantics of detection streams.
- Flags like `enable_unknown_object_motion_output`, `enable_unknown_object_velocity_estimation`: additional logic, but already covered conceptually by other “enable/disable extra work” flags across nodes.

Rationale: additional flags/matrices strongly affect tracking semantics and tuning space; we restrict sweeps to core rate/lifetime knobs for latency.

---

### `map_based_prediction` (`map_based_prediction`)

**Swept (present)**:

- `prediction_time_horizon_vehicle`
- `prediction_sampling_delta_time`
- `reference_path_resolution`
- `history_time_length`
- `object_buffer_time_length`

These control time horizon, temporal sampling, reference path resolution, and history window – all first-order drivers of prediction workload.

**Other params**:

- Remaining config entries are mostly object-type thresholds, classification semantics, and topic routes.

Rationale: additional thresholds are more about *which* objects to predict rather than **how much computation per object**, given a fixed bag.

---

### `behavior_path_planner` (`autoware_behavior_path_planner_node`)

**Swept (present)**:

- `planning_hz`
- `forward_path_length`
- `input_path_interval`
- `output_path_interval`

These define planning frequency, path length, and sampling density.

**Other params (not swept)**:

- Numerous behavior-specific thresholds (lane change gaps, safety margins, etc.) in the full Autoware config – they influence decision making and safety, not straightforwardly the cost of a single replan on a fixed scenario.

Rationale: exploring all behavior thresholds would explode the search space; the chosen four already cover latency sensitivity to how long/often the planner runs and how dense the path is.

---

### `autonomous_emergency_braking` (`autoware_autonomous_emergency_braking`)

**Swept (present)** – from the AEB param file:

- `voxel_grid_x`
- `voxel_grid_y`
- `cluster_tolerance`
- `aeb_hz`
- `mpc_prediction_time_horizon`

These affect pointcloud density, clustering workload, update rate, and prediction horizon.

**Other params (not swept)**:

- Safety thresholds (e.g., braking distances), MPC penalty weights, and comfort parameters.

Rationale: these are critical for safety/behavior correctness, but their impact on CPU cost is indirect and scenario dependent; we keep the sweep focused on clearly structural cost drivers.

---

### `velocity_smoother` (`velocity_smoother_node`)

**Swept (present)**:

- `resample_ds`
- `max_trajectory_length`
- `dense_resample_dt`
- `extract_ahead_dist`

These parameters control how many trajectory points are considered and at what temporal spacing.

**Other params (not swept)**:

- Jerk/accel limits, speed constraints, and comfort/safety tuning.

Rationale: while important for control quality, these do not systematically change the number of points processed; we treat path density and length as the primary latency knobs.

---

### `pointcloud_concatenate_data` (`concatenate_and_time_sync_node`)

**Swept (present)**:

- `timeout_sec`
- `maximum_queue_size`

They set buffering and queue depth, affecting synchronization behavior and buffer sizes.

**Other params (not swept)**:

- Frame/topic names and QoS settings from the full Autoware config.

Rationale: on a fixed bag, queue size and timeout are the two levers that realistically change how much message processing happens per run.

---

### `trajectory_follower_controller` (`controller_node_exe`)

**Swept (present)**:

- `ctrl_period`
- `timeout_thr_sec`

These determine control loop rate and timeout behavior.

**Other params (not swept)**:

- MPC/PID gains and cost weights: crucial for control performance, but computationally inexpensive and not the main CPU bottleneck for this node.

Rationale: control loop frequency and timeout are the knobs with clear, monotonic impact on runtime.

---

### `mission_planner` (`mission_planner`)

**Swept (present)**:

- `reroute_time_threshold`
- `minimum_reroute_length`

They govern how often rerouting logic is triggered and under what spatial conditions.

**Other params (not swept)**:

- Numerous arrival/goal/lane conditions (angles, distances, enabling specific behaviors).

Rationale: with a fixed scenario, these mainly affect *if* certain code paths are exercised, not the basic cost of a single reroute. We keep the sweep to the primary rerouting frequency/distance knobs.

Note: we inject `arrival_check_distance` at runtime to satisfy a statically-typed parameter requirement, but we do not sweep it.

---

### `shape_estimation` (`shape_estimation_node`)

**Swept (present)**:

- `use_filter`
- `use_boost_bbox_optimizer`

These toggle additional filtering and bounding-box optimization logic per object.

**Other params (not swept)** – from `/perception/object_recognition/detection/clustering/shape_estimation.ros__parameters`:

- `use_corrector`, `use_vehicle_reference_shape_size`, `use_vehicle_reference_yaw`: smaller adjustments to how shapes are corrected relative to the vehicle; less obviously heavy than optimizer/filter toggles.
- `model_params.use_ml_shape_estimator` / `model_path`: ML estimator path is not usable without a valid model_path, and enabling it currently causes `UninitializedStaticallyTypedParameterException`.

Rationale: the two swept flags already span “cheap vs. more expensive” processing modes; ML shape estimation would be interesting but cannot be safely enabled with the current deployment.

---

### `lidar_centerpoint` (`autoware_lidar_centerpoint_node`)

**Swept (present)**:

- `densification_params.num_past_frames`
- `cloud_capacity`
- `post_process_params.circle_nms_dist_threshold`

These control temporal stacking of frames, maximum point cloud capacity, and NMS distance – all key performance drivers.

**Other params (not swept)**:

- Engine/ONNX paths, network architecture details, various score/threshold parameters.

Rationale: sweeping model architecture or thresholds would effectively cross into model/tuning experiments; for latency, number of frames, capacity, and NMS distance are sufficient.

---

### `motion_velocity_planner` (`autoware_motion_velocity_planner_node`)

**Swept (present)** – across the two YAML documents in `motion_velocity_planner.param.yaml`:

- `pointcloud_preprocessing.downsample_by_voxel_grid.voxel_size_x`
- `pointcloud_preprocessing.downsample_by_voxel_grid.voxel_size_y`
- `trajectory_polygon_collision_check.decimate_trajectory_step_length`
- `pointcloud_preprocessing.euclidean_clustering.cluster_tolerance`

These mainly affect pointcloud density and collision-checking path resolution.

**Other params (not swept)**:

- Many MPC weight and RSS/safety parameters (e.g., `over_s_*_weight`, prediction horizons inside the optimization-based planner, various thresholds in `obstacle_filtering` and `yield`).

Rationale: these tune safety/comfort and constraint tightness, but with a fixed bag their CPU impact is indirect. For our latency focus, we sweep parameters that directly change the size of the optimization/collision-check problems.

Note: we inject `wheel_radius` at runtime to satisfy a statically-typed parameter; we do not sweep it.

