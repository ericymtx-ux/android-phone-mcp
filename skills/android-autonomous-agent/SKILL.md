---
name: android-autonomous-agent
description: Autonomous Android agent powered by visual reasoning. Capable of executing high-level tasks on an Android device by autonomously capturing screenshots, analyzing UI with Volcengine vision models, planning actions, and executing them via ADB/uiautomator2.
argument-hint: "[task description] [max_steps]"
---

# Android Autonomous Agent

This skill allows you to execute complex, multi-step operations on an Android phone using visual reasoning. It is powered by `android-phone-mcp` and Volcengine vision models.

## When to use
- You need to perform complex, multi-step operations on an Android phone.
- The task requires visual understanding of the app interface (e.g., "Find the red button", "Read the stock price").
- The target app does not have a direct API or deep link.

## Usage

```bash
# Basic usage
android-agent run "Open WeChat and send a message to Mom saying I'll be home for dinner"

# Eco Mode (Saves tokens by using lower resolution screenshots and stricter history pruning)
android-agent run "Open stock app and check K-line" --eco
```

## Action Space

## How it works
1.  **Observation**: Captures a screenshot of the current device state.
2.  **Reasoning**: Sends the screenshot and history to the Volcengine Vision Model to decide the next action.
3.  **Execution**: Performs the action (click, scroll, type, etc.) on the device via ADB.
4.  **Loop**: Repeats the process until the goal is achieved or max steps are reached.

## Parameters
- `goal` (string): The high-level task description.
- `max_steps` (integer, optional): Maximum number of steps to attempt (default: 50).

## Dependencies
- `android-phone-mcp` server must be running and connected to OpenClaw/Claude.
- An Android device must be connected via ADB.
- `ARK_API_KEY` must be set in the environment.
