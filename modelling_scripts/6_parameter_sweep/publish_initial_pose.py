#!/usr/bin/env python3
"""
Publish initial pose (PoseWithCovarianceStamped) to EKF and NDT topics repeatedly
so that nodes started in isolation receive it when they subscribe.
Run with same ROS environment as the sweep. Exits after duration_sec.
Pass --use-sim-time to use /clock (required when nodes use use_sim_time).
"""
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from geometry_msgs.msg import PoseWithCovarianceStamped
import sys
import time


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    use_sim_time = "--use-sim-time" in sys.argv
    duration_sec = float(args[0]) if args else 20.0
    interval = 0.5

    rclpy.init()
    node = Node("initial_pose_publisher")
    if use_sim_time:
        node.set_parameters([Parameter("use_sim_time", Parameter.Type.BOOL, True)])

    pub_ekf = node.create_publisher(
        PoseWithCovarianceStamped,
        "/localization/pose_twist_fusion_filter/initialpose",
        10,
    )
    pub_ndt = node.create_publisher(
        PoseWithCovarianceStamped,
        "/localization/pose_estimator/ekf_pose_with_covariance",
        10,
    )

    msg = PoseWithCovarianceStamped()
    msg.header.frame_id = "map"
    msg.pose.pose.position.x = 0.0
    msg.pose.pose.position.y = 0.0
    msg.pose.pose.position.z = 0.0
    msg.pose.pose.orientation.x = 0.0
    msg.pose.pose.orientation.y = 0.0
    msg.pose.pose.orientation.z = 0.0
    msg.pose.pose.orientation.w = 1.0
    msg.pose.covariance = [
        0.25, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.25, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.25, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.017453292519943295,
    ]

    start = time.monotonic()
    count = 0
    while (time.monotonic() - start) < duration_sec:
        t = node.get_clock().now()
        msg.header.stamp.sec = int(t.seconds_nanoseconds()[0])
        msg.header.stamp.nanosec = int(t.seconds_nanoseconds()[1])
        pub_ekf.publish(msg)
        pub_ndt.publish(msg)
        count += 1
        time.sleep(interval)
        rclpy.spin_once(node, timeout_sec=0)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
