# import firebase_admin
# from firebase_admin import credentials, firestore
# from flask import Flask, request, jsonify, render_template, Response
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# import os
# import importlib.util
# import sys
# from pathlib import Path
# import inspect
# import json
# import time
# import threading
# import requests
# import traceback

# # Initialize Flask app
# app = Flask(__name__)

# # Initialize Firebase Admin SDK
# cred = credentials.Certificate("firebase_credentials.json")
# firebase_admin.initialize_app(cred)
# db = firestore.client()

# # Selenium WebDriver setup
# def get_driver():
#     options = Options()
#     # options.add_argument("--headless")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     driver = webdriver.Chrome(
#         service=Service(r"C:\Users\Admin\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"),
#         options=options
#     )
#     return driver

# # Directory for action scripts
# ACTIONS_DIR = Path("actions")
# ACTIONS_DIR.mkdir(exist_ok=True)

# # Helper function to extract parameter names and types from action script
# def get_action_params(action_name):
#     script_path = ACTIONS_DIR / f"{action_name}.py"
#     if not script_path.exists():
#         return {}
#     spec = importlib.util.spec_from_file_location(action_name, script_path)
#     module = importlib.util.module_from_spec(spec)
#     sys.modules[action_name] = module
#     spec.loader.exec_module(module)
#     action_func = getattr(module, action_name, None)
#     if action_func is None:
#         return {}
#     sig = inspect.signature(action_func)
#     params = {}
#     for param in sig.parameters.values():
#         param_type = param.annotation.__name__ if param.annotation != inspect._empty else "str"
#         if param_type in ["str", "int", "float"]:
#             params[param.name] = param_type
#     return params

# # Validate Python script for allowed modules and functions
# def validate_script(script_content):
#     try:
#         return True, "Script validated successfully"
#     except SyntaxError:
#         return False, "Invalid Python syntax"

# # Helper function to wait until page is fully loaded
# def wait_until_page_fully_loaded(driver, timeout=10):
#     try:
#         end_time = time.time() + timeout
#         while time.time() < end_time:
#             ready_state = driver.execute_script("return document.readyState")
#             if ready_state == "complete":
#                 return {"status": "success", "message": "Page fully loaded"}
#             time.sleep(0.5)
#         return {"status": "error", "message": "Timed out waiting for page to load"}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# # Helper function to execute an action script
# def execute_action(action_name, parameters, driver):
#     try:
#         script_path = ACTIONS_DIR / f"{action_name}.py"
#         if not script_path.exists():
#             return {"error": f"Action script {action_name}.py not found"}
        
#         wait_until_page_fully_loaded(driver, 20)
#         spec = importlib.util.spec_from_file_location(action_name, script_path)
#         module = importlib.util.module_from_spec(spec)
#         sys.modules[action_name] = module
#         spec.loader.exec_module(module)
#         time.sleep(5)
        
#         action_func = getattr(module, action_name, None)
#         if not action_func:
#             return {"error": f"Function {action_name} not found in {action_name}.py"}
        
#         result = action_func(driver, **parameters)
#         print(result)
#         return {"status": result["status"], "result": result, "interacted_elements": result.get("interacted_elements", [])}
#     except Exception as e:
#         return {"error": str(e)}

# # Function to count elements on a page
# def count_elements(driver, url):
#     driver.get(url)
#     wait_until_page_fully_loaded(driver)
#     buttons = driver.find_elements(By.TAG_NAME, "button")
#     inputs = driver.find_elements(By.TAG_NAME, "input")
#     links = driver.find_elements(By.TAG_NAME, "a")
#     return {
#         "buttons": len(buttons),
#         "inputs": len(inputs),
#         "links": len(links)
#     }

# # Function to run the entire test case
# def run_testcase(testcase_data, driver, testcase_id):
#     actions = testcase_data.get("actions", [])
#     if not actions:
#         result = {"message": "No actions to run", "status": "skipped", "results": [], "timestamp": int(time.time() * 1000)}
#         db.collection("test_results").document(testcase_id).collection("runs").document(str(int(time.time() * 1000))).set(result)
#         return result
    
#     results = []
#     driver.get(testcase_data.get("proj_url"))
#     run_id = str(int(time.time() * 1000))
    
#     # Set initial "running" status
#     db.collection("test_results").document(testcase_id).collection("runs").document(run_id).set({"status": "running", "results": [], "timestamp": int(time.time() * 1000)})
    
#     for action_item in actions:
#         action_id = action_item.get("action_id")
#         instance_id = action_item.get("instance_id")
#         parameters = action_item.get("parameters")
        
#         action_doc = db.collection("actions").document(action_id).get()
#         if not action_doc.exists:
#             action_result = {
#                 "action_id": action_id,
#                 "instance_id": instance_id,
#                 "name": "Unknown",
#                 "status": "error",
#                 "details": {"error": "Action not found"}
#             }
#             results.append(action_result)
#             db.collection("test_results").document(testcase_id).collection("runs").document(run_id).set({"status": "running", "results": results, "timestamp": int(time.time() * 1000)}, merge=True)
#             continue
        
#         action_name = action_doc.to_dict().get("script_file").split(".")[0]
#         result = execute_action(action_name, parameters, driver)
#         action_result = {
#             "action_id": action_id,
#             "instance_id": instance_id,
#             "name": action_name,
#             "status": "passed" if "error" not in result else "failed",
#             "details": result.get("result", result.get("error", "No details")),
#             "interacted_elements": result.get("interacted_elements", [])
#         }
#         results.append(action_result)
#         # Update Firestore in real-time with status
#         db.collection("test_results").document(testcase_id).collection("runs").document(run_id).set({"status": "running", "results": results, "timestamp": int(time.time() * 1000)}, merge=True)
    
#     # Determine final status
#     try:
#         success_element = driver.find_element(By.XPATH, "//*[contains(text(), 'success')]")
#         overall_status = "passed" if success_element else "failed"
#     except:
#         overall_status = "failed" if any(r["status"] == "error" for r in results) else "passed"
    
#     final_result = {"message": "Testcase executed", "status": overall_status, "results": results, "timestamp": int(time.time() * 1000)}
#     db.collection("test_results").document(testcase_id).collection("runs").document(run_id).set(final_result)
#     return final_result

# # Fetch past test results
# @app.route("/past-results/<testcase_id>", methods=["GET"])
# def get_past_results(testcase_id):
#     testcase = db.collection("testcases").document(testcase_id).get()
#     if not testcase.exists:
#         return jsonify({"error": "Testcase not found"}), 404
    
#     runs_ref = db.collection("test_results").document(testcase_id).collection("runs")
#     past_results = [doc.to_dict() for doc in runs_ref.stream()]
#     past_results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)  # Sort by timestamp, newest first
#     return jsonify(past_results)

# # Render past results page
# @app.route("/past-results/<proj_id>/<testcase_id>")
# def past_results(proj_id, testcase_id):
#     project = db.collection("projects").document(proj_id).get()
#     if not project.exists:
#         return jsonify({"error": "Project not found"}), 404
#     testcase = db.collection("testcases").document(testcase_id).get()
#     if not testcase.exists or testcase.to_dict().get("proj_id") != proj_id:
#         return jsonify({"error": "Testcase not found or does not belong to project"}), 404
#     return render_template("past_results.html", proj_id=proj_id, testcase_id=testcase_id, testcase_name=testcase.to_dict().get("name"))

# # Upload new action
# @app.route("/addaction/", methods=["POST"])
# def add_action():
#     action_name = request.form.get("name")
#     script_file = request.files.get("script")

#     if not (script_file and action_name):
#         return jsonify({"error": "Script file and action name are required"}), 400
    
#     script_content = script_file.read().decode('utf-8')
#     is_valid, message = validate_script(script_content)
#     if not is_valid:
#         return jsonify({"error": message}), 400
    
#     filename = f"{action_name}.py"
#     file_path = ACTIONS_DIR / filename
#     with open(file_path, "w") as file:
#         file.write(script_content)
    
#     if not file_path.exists():
#         return jsonify({"error": "Failed to save action file"}), 500
    
#     parameters_types = get_action_params(action_name)
#     if not parameters_types:
#         return jsonify({"error": "No valid action function found or failed to extract parameters"}), 400
    
#     action_id = db.collection("actions").document().id
#     db.collection("actions").document(action_id).set({
#         "action_name": action_name,
#         "script_file": filename,
#         "parameters": parameters_types
#     })
    
#     return jsonify({
#         "message": "Action uploaded successfully",
#         "action_id": action_id,
#         "action_name": action_name
#     })

# # View action details
# @app.route("/dashboard/<proj_id>/<testcase_id>/<action_id>", methods=["GET"])
# def view_action(proj_id, testcase_id, action_id):
#     project = db.collection("projects").document(proj_id).get()
#     if not project.exists:
#         return jsonify({"error": "Project not found"}), 404
    
#     testcase = db.collection("testcases").document(testcase_id).get()
#     if not testcase.exists or testcase.to_dict().get("proj_id") != proj_id:
#         return jsonify({"error": "Testcase not found or does not belong to project"}), 404
    
#     action_ref = db.collection("actions").document(action_id).get()
#     if not action_ref.exists:
#         return jsonify({"error": "Action not found"}), 404
    
#     action_data = action_ref.to_dict()
#     return render_template(
#         "action_details.html",
#         proj_id=proj_id,
#         testcase_id=testcase_id,
#         action_id=action_id,
#         action_name=action_data.get("action_name"),
#         script_file=action_data.get("script_file"),
#         parameters=action_data.get("parameters", {})
#     )

# # Project management endpoints
# @app.route("/dashboard/", methods=["GET", "POST"])
# def dashboard():
#     if request.method == "GET":
#         projects_ref = db.collection("projects")
#         return render_template("projects.html", projects=[
#             {"id": doc.id, "name": doc.to_dict().get("name")} for doc in projects_ref.stream()
#         ])
    
#     elif request.method == "POST":
#         data = request.get_json()
#         action = data.get("action")
        
#         if action == "add_project":
#             name = data.get("name")
#             if not name:
#                 return jsonify({"error": "Project name is required"}), 400
#             existing = db.collection("projects").where("name", "==", name).stream()
#             for doc in existing:
#                 return jsonify({"message": "Project already exists", "proj_id": doc.id})
#             proj_id = db.collection("projects").document().id
#             db.collection("projects").document(proj_id).set({"name": name})
#             return jsonify({"message": "Project created", "proj_id": proj_id})
        
#         elif action == "remove_project":
#             proj_id = data.get("proj_id")
#             if not proj_id:
#                 return jsonify({"error": "proj_id is required"}), 400
#             project = db.collection("projects").document(proj_id).get()
#             if not project.exists:
#                 return jsonify({"error": "Project not found"}), 404
#             db.collection("projects").document(proj_id).delete()
#             testcases = db.collection("testcases").where("proj_id", "==", proj_id).stream()
#             for tc in testcases:
#                 db.collection("test_results").document(tc.id).delete()  # Clean up results
#                 db.collection("testcases").document(tc.id).delete()
#             return jsonify({"message": "Project removed"})
        
#         elif action == "select_project":
#             proj_id = data.get("proj_id")
#             if not proj_id:
#                 return jsonify({"error": "proj_id is required"}), 400
#             project = db.collection("projects").document(proj_id).get()
#             if not project.exists:
#                 return jsonify({"error": "Project not found"}), 404
#             return jsonify({"proj_id": proj_id, "name": project.to_dict().get("name")})
        
#         return jsonify({"error": "Invalid action"}), 400

# # Test case management endpoints
# @app.route("/dashboard/<proj_id>", methods=["GET", "POST"])
# def project_dashboard(proj_id):
#     project = db.collection("projects").document(proj_id).get()
#     if not project.exists:
#         return jsonify({"error": "Project not found"}), 404
    
#     if request.method == "GET":
#         testcases_ref = db.collection("testcases").where("proj_id", "==", proj_id)
#         testcases = [
#             {"id": doc.id, "name": doc.to_dict().get("name"), "proj_url": doc.to_dict().get("proj_url")}
#             for doc in testcases_ref.stream()
#         ]
#         return render_template("testcases.html", proj_id=proj_id, proj_name=project.to_dict().get("name"), testcases=testcases)    
#     elif request.method == "POST":
#         data = request.get_json()
#         if not data:
#             return jsonify({"error": "Invalid JSON"}), 400
#         action = data.get("action")
        
#         if action == "add_testcase":
#             name = data.get("name")
#             proj_url = data.get("proj_url")
#             if not (name and proj_url):
#                 return jsonify({"error": "name and proj_url are required"}), 400
#             existing = db.collection("testcases").where("proj_id", "==", proj_id).where("name", "==", name).stream()
#             for doc in existing:
#                 return jsonify({"error": "Testcase name already exists in this project", "testcase_id": doc.id}), 400
#             testcase_id = db.collection("testcases").document().id
#             db.collection("testcases").document(testcase_id).set({
#                 "proj_id": proj_id,
#                 "name": name,
#                 "proj_url": proj_url,
#                 "actions": []
#             })
#             return jsonify({"message": "Testcase created", "testcase_id": testcase_id})
        
#         elif action == "remove_testcase":
#             testcase_id = data.get("testcase_id")
#             if not testcase_id:
#                 return jsonify({"error": "testcase_id is required"}), 400
#             testcase = db.collection("testcases").document(testcase_id).get()
#             if not testcase.exists or testcase.to_dict().get("proj_id") != proj_id:
#                 return jsonify({"error": "Testcase not found or does not belong to project"}), 404
#             db.collection("test_results").document(testcase_id).delete()  # Clean up results
#             db.collection("testcases").document(testcase_id).delete()
#             return jsonify({"message": "Testcase removed"})
        
#         elif action == "select_testcase":
#             testcase_id = data.get("testcase_id")
#             if not testcase_id:
#                 return jsonify({"error": "testcase_id is required"}), 400
#             testcase = db.collection("testcases").document(testcase_id).get()
#             if not testcase.exists or testcase.to_dict().get("proj_id") != proj_id:
#                 return jsonify({"error": "Testcase not found or does not belong to project"}), 404
#             return jsonify({"testcase_id": testcase_id, "name": testcase.to_dict().get("name")})
        
#         return jsonify({"error": "Invalid action"}), 400

# # Run test case in a background thread
# @app.route("/run-testcase/<testcase_id>", methods=["POST"])
# def run_testcase_endpoint(testcase_id):
#     testcase = db.collection("testcases").document(testcase_id).get()
#     if not testcase.exists:
#         return jsonify({"error": "Testcase not found"}), 404
    
#     # Initialize the result in Firestore
#     db.collection("test_results").document(testcase_id).set({"status": "running", "results": []})
    
#     def run_testcase_task():
#         driver = get_driver()
#         try:
#             result = run_testcase(testcase.to_dict(), driver, testcase_id)
#         finally:
#             driver.quit()
    
#     thread = threading.Thread(target=run_testcase_task)
#     thread.start()
#     return jsonify({"message": "Test case running", "testcase_id": testcase_id})

# # Fetch test case results
# @app.route("/get-results/<testcase_id>", methods=["GET"])
# def get_results(testcase_id):
#     result_doc = db.collection("test_results").document(testcase_id).get()
#     if not result_doc.exists:
#         return jsonify({"status": "pending"})
#     return jsonify(result_doc.to_dict())

# # Render results page
# @app.route("/results/<proj_id>/<testcase_id>")
# def results(proj_id, testcase_id):
#     project = db.collection("projects").document(proj_id).get()
#     if not project.exists:
#         return jsonify({"error": "Project not found"}), 404
#     testcase = db.collection("testcases").document(testcase_id).get()
#     if not testcase.exists or testcase.to_dict().get("proj_id") != proj_id:
#         return jsonify({"error": "Testcase not found or does not belong to project"}), 404
#     return render_template("results.html", proj_id=proj_id, testcase_id=testcase_id, testcase_name=testcase.to_dict().get("name"))

# # Elements Summary Report for a single test case
# @app.route("/elements-summary/<testcase_id>", methods=["GET"])
# def elements_summary(testcase_id):
#     testcase = db.collection("testcases").document(testcase_id).get()
#     if not testcase.exists:
#         return jsonify({"error": "Testcase not found"}), 404
#     url = testcase.to_dict().get("proj_url")
    
#     # Count total elements using Selenium
#     driver = get_driver()
#     total_elements = count_elements(driver, url)
#     driver.quit()
    
#     # Fetch all passed test runs for this testcase
#     runs_ref = db.collection("test_results").document(testcase_id).collection("runs").where("status", "==", "passed").stream()
#     tested_elements = set()
#     for run in runs_ref:
#         run_data = run.to_dict()
#         for result in run_data.get("results", []):
#             for elem in result.get("interacted_elements", []):
#                 tested_elements.add(elem)
    
#     # Calculate tested counts
#     tested_buttons = sum(1 for e in tested_elements if "button" in e.lower())
#     tested_inputs = sum(1 for e in tested_elements if "input" in e.lower())
#     tested_links = sum(1 for e in tested_elements if "/A[" in e)
    
#     # Calculate percentages
#     total_all = total_elements["buttons"] + total_elements["inputs"] + total_elements["links"]
#     tested_all = tested_buttons + tested_inputs + tested_links
#     coverage_percentage = (tested_all / total_all * 100) if total_all > 0 else 0
#     button_percentage = (tested_buttons / total_elements["buttons"] * 100) if total_elements["buttons"] > 0 else 0
#     input_percentage = (tested_inputs / total_elements["inputs"] * 100) if total_elements["inputs"] > 0 else 0
#     link_percentage = (tested_links / total_elements["links"] * 100) if total_elements["links"] > 0 else 0
    
#     report_data = {
#         "url": url,
#         "testcase_name": testcase.to_dict().get("name"),
#         "elements": [
#             {"type": "Buttons", "total": total_elements["buttons"], "tested": tested_buttons, "percentage": round(button_percentage, 2)},
#             {"type": "Inputs", "total": total_elements["inputs"], "tested": tested_inputs, "percentage": round(input_percentage, 2)},
#             {"type": "Links", "total": total_elements["links"], "tested": tested_links, "percentage": round(link_percentage, 2)}
#         ],
#         "summary": {
#             "total_elements": total_all,
#             "tested_elements": tested_all,
#             "coverage_percentage": round(coverage_percentage, 2)
#         }
#     }
#     return render_template("elements_summary.html", report=report_data)

# # Project-level Elements Summary Report
# @app.route("/project-elements-summary/<proj_id>", methods=["GET"])
# def project_elements_summary(proj_id):
#     project = db.collection("projects").document(proj_id).get()
#     if not project.exists:
#         return jsonify({"error": "Project not found"}), 404
    
#     # Fetch all test cases for the project
#     testcases_ref = db.collection("testcases").where("proj_id", "==", proj_id).stream()
#     testcases = [(doc.id, doc.to_dict()) for doc in testcases_ref]
    
#     if not testcases:
#         return jsonify({"error": "No test cases found for this project"}), 404
    
#     # Group test cases by URL
#     url_to_testcases = {}
#     for testcase_id, testcase_data in testcases:
#         url = testcase_data.get("proj_url")
#         if url not in url_to_testcases:
#             url_to_testcases[url] = []
#         url_to_testcases[url].append((testcase_id, testcase_data))
    
#     driver = get_driver()
#     reports = []
#     project_summary = {"buttons": {"total": 0, "tested": 0}, "inputs": {"total": 0, "tested": 0}, "links": {"total": 0, "tested": 0}}
    
#     # Process each URL
#     for url, testcase_list in url_to_testcases.items():
#         # Count total elements for this URL
#         total_elements = count_elements(driver, url)
        
#         # Aggregate tested elements across all test cases for this URL
#         tested_elements = set()
#         for testcase_id, _ in testcase_list:
#             runs_ref = db.collection("test_results").document(testcase_id).collection("runs").where("status", "==", "passed").stream()
#             for run in runs_ref:
#                 run_data = run.to_dict()
#                 for result in run_data.get("results", []):
#                     for elem in result.get("interacted_elements", []):
#                         tested_elements.add(elem)
        
#         # Calculate tested counts
#         tested_buttons = sum(1 for e in tested_elements if "button" in e.lower())
#         tested_inputs = sum(1 for e in tested_elements if "input" in e.lower())
#         tested_links = sum(1 for e in tested_elements if "/A[" in e)
        
#         # Calculate percentages
#         total_all = total_elements["buttons"] + total_elements["inputs"] + total_elements["links"]
#         tested_all = tested_buttons + tested_inputs + tested_links
#         coverage_percentage = (tested_all / total_all * 100) if total_all > 0 else 0
#         button_percentage = (tested_buttons / total_elements["buttons"] * 100) if total_elements["buttons"] > 0 else 0
#         input_percentage = (tested_inputs / total_elements["inputs"] * 100) if total_elements["inputs"] > 0 else 0
#         link_percentage = (tested_links / total_elements["links"] * 100) if total_elements["links"] > 0 else 0
        
#         # Update project summary
#         project_summary["buttons"]["total"] += total_elements["buttons"]
#         project_summary["buttons"]["tested"] += tested_buttons
#         project_summary["inputs"]["total"] += total_elements["inputs"]
#         project_summary["inputs"]["tested"] += tested_inputs
#         project_summary["links"]["total"] += total_elements["links"]
#         project_summary["links"]["tested"] += tested_links
        
#         report_data = {
#             "url": url,
#             "testcases": [{"id": tc_id, "name": tc_data.get("name")} for tc_id, tc_data in testcase_list],
#             "elements": [
#                 {"type": "Buttons", "total": total_elements["buttons"], "tested": tested_buttons, "percentage": round(button_percentage, 2)},
#                 {"type": "Inputs", "total": total_elements["inputs"], "tested": tested_inputs, "percentage": round(input_percentage, 2)},
#                 {"type": "Links", "total": total_elements["links"], "tested": tested_links, "percentage": round(link_percentage, 2)}
#             ],
#             "summary": {
#                 "total_elements": total_all,
#                 "tested_elements": tested_all,
#                 "coverage_percentage": round(coverage_percentage, 2)
#             }
#         }
#         reports.append(report_data)
    
#     driver.quit()
    
#     # Calculate project-wide summary statistics
#     project_total = project_summary["buttons"]["total"] + project_summary["inputs"]["total"] + project_summary["links"]["total"]
#     project_tested = project_summary["buttons"]["tested"] + project_summary["inputs"]["tested"] + project_summary["links"]["tested"]
#     project_coverage = (project_tested / project_total * 100) if project_total > 0 else 0
#     project_summary["total_elements"] = project_total
#     project_summary["tested_elements"] = project_tested
#     project_summary["coverage_percentage"] = round(project_coverage, 2)
#     project_summary["buttons"]["percentage"] = round((project_summary["buttons"]["tested"] / project_summary["buttons"]["total"] * 100) if project_summary["buttons"]["total"] > 0 else 0, 2)
#     project_summary["inputs"]["percentage"] = round((project_summary["inputs"]["tested"] / project_summary["inputs"]["total"] * 100) if project_summary["inputs"]["total"] > 0 else 0, 2)
#     project_summary["links"]["percentage"] = round((project_summary["links"]["tested"] / project_summary["links"]["total"] * 100) if project_summary["links"]["total"] > 0 else 0, 2)
    
#     return render_template("project_elements_summary.html", project_name=project.to_dict().get("name"), reports=reports, project_summary=project_summary)

# @app.route("/dashboard/<proj_id>/<testcase_id>", methods=["GET", "POST"])
# def testcase_dashboard(proj_id, testcase_id):
#     project = db.collection("projects").document(proj_id).get()
#     if not project.exists:
#         return jsonify({"error": "Project not found"}), 404
#     testcase = db.collection("testcases").document(testcase_id).get()
#     if not testcase.exists or testcase.to_dict().get("proj_id") != proj_id:
#         return jsonify({"error": "Testcase not found or does not belong to project"}), 404
    
#     if request.method == "GET":
#         testcase_data = testcase.to_dict()
#         actions_ref = db.collection("actions")
#         actions = {  
#             doc.id: {"id": doc.id, "name": doc.to_dict().get("action_name"), "parameters": doc.to_dict().get("parameters", {})}
#             for doc in actions_ref.stream()
#         }
#         res = testcase_data.get("actions", [])
#         for action in res:
#             action["name"] = actions[action['action_id']]['name']
#         return render_template(
#             "testcase_details.html",
#             proj_id=proj_id,
#             testcase_id=testcase_id,
#             testcase_name=testcase_data.get("name"),
#             proj_url=testcase_data.get("proj_url"),
#             actions=testcase_data.get("actions", []),
#             available_actions=list(actions.values())
#         )
    
#     elif request.method == "POST":
#         data = request.get_json(silent=True)
#         if data:
#             action = data.get("action")
            
#             if action == "add_action":
#                 action_id = data.get("action_id")
#                 parameters = data.get("parameters", {})
#                 if not action_id:
#                     return jsonify({"error": "action_id is required"}), 400
                
#                 action_doc = db.collection("actions").document(action_id).get()
#                 if not action_doc.exists:
#                     return jsonify({"error": "Action not found"}), 404
                
#                 expected_params = action_doc.to_dict().get("parameters", {})
#                 for param in expected_params.keys():
#                     if param not in parameters:
#                         return jsonify({"error": f"Missing parameter: {param}"}), 400
#                     if expected_params[param] == "int":
#                         try:
#                             parameters[param] = int(parameters[param])
#                         except ValueError:
#                             return jsonify({"error": f"Parameter {param} must be an integer"}), 400
#                     elif expected_params[param] == "float":
#                         try:
#                             parameters[param] = float(parameters[param])
#                         except ValueError:
#                             return jsonify({"error": f"Parameter {param} must be a float"}), 400
#                     elif expected_params[param] != "str":
#                         return jsonify({"error": f"Unsupported type {expected_params[param]} for parameter {param}"}), 400
                
#                 testcase_ref = db.collection("testcases").document(testcase_id)
#                 testcase_ref.update({
#                     "actions": firestore.ArrayUnion([{
#                         "action_id": action_id,
#                         "parameters": parameters
#                     }])
#                 })
#                 return jsonify({"message": "Action added"})
            
#             elif action == "update_actions":
#                 new_actions = data.get("actions", [])
#                 if not isinstance(new_actions, list):
#                     return jsonify({"error": "actions must be a list"}), 400
#                 for action_item in new_actions:
#                     if not isinstance(action_item, dict) or "action_id" not in action_item or "parameters" not in action_item:
#                         return jsonify({"error": "Each action must have action_id and parameters"}), 400
#                     action_doc = db.collection("actions").document(action_item["action_id"]).get()
#                     if not action_doc.exists:
#                         return jsonify({"error": f"Action {action_item['action_id']} not found"}), 404
#                     expected_params = action_doc.to_dict().get("parameters", {})
#                     for param in expected_params.keys():
#                         if param not in action_item["parameters"]:
#                             return jsonify({"error": f"Missing parameter: {param} for action {action_item['action_id']}"}), 400
#                         if expected_params[param] == "int":
#                             try:
#                                 action_item["parameters"][param] = int(action_item["parameters"][param])
#                             except ValueError:
#                                 return jsonify({"error": f"Parameter {param} must be an integer for action {action_item['action_id']}"}), 400
#                         elif expected_params[param] == "float":
#                             try:
#                                 action_item["parameters"][param] = float(action_item["parameters"][param])
#                             except ValueError:
#                                 return jsonify({"error": f"Parameter {param} must be a float for action {action_item['action_id']}"}), 400
#                         elif expected_params[param] != "str":
#                             return jsonify({"error": f"Unsupported type {expected_params[param]} for parameter {param} for action {action_item['action_id']}"}), 400
#                 testcase_ref = db.collection("testcases").document(testcase_id)
#                 testcase_ref.update({"actions": new_actions})
#                 return jsonify({"message": "Testcase actions updated"})
            
#             elif action == "run_testcase":
#                 return run_testcase_endpoint(testcase_id)
        
#         return jsonify({"error": "Invalid action or request format"}), 400

# @app.route("/dashboard/<proj_id>/testcases", methods=["GET"])
# def view_testcases(proj_id):
#     project = db.collection("projects").document(proj_id).get()
#     if not project.exists:
#         return jsonify({"error": "Project not found"}), 404
#     testcases = db.collection("testcases").where("proj_id", "==", proj_id).stream()
#     testcase_list = [{"id": tc.id, "name": tc.to_dict().get("name"), "proj_url": tc.to_dict().get("proj_url")} for tc in testcases]
#     return render_template("testcases.html", proj_id=proj_id, testcases=testcase_list)

# @app.route("/newaction/", methods=["GET"])
# def new_action():
#     proj_id = request.args.get("proj_id")
#     testcase_id = request.args.get("testcase_id")
#     return render_template("actions_view.html", proj_id=proj_id, testcase_id=testcase_id)

# @app.route('/proxy')
# def proxy():
#     url = request.args.get('url')
#     if not url:
#         return "Missing 'url' parameter", 400
#     print("Fetching URL:", url)
#     try:
#         session = requests.Session()
#         session.headers.update({"User-Agent": "Mozilla/5.0"})
#         response = session.get(url, allow_redirects=True)
#         content_type = response.headers.get('Content-Type', 'text/html')
#         return Response(response.content, content_type=content_type)
#     except Exception as e:
#         print("Error:", str(e))
#         traceback.print_exc()
#         return f"Error fetching content: {str(e)}", 500

# @app.route('/capture_xpath', methods=['POST'])
# def capture_xpath():
#     data = request.get_json()
#     xpath = data.get('xpath')
#     print(f"Captured XPath: {xpath}")
#     return Response("Received XPath", status=200, mimetype='text/plain')

# # Chatbot integration
# GEMINI_API_KEY = "AIzaSyBpsEsyY3sxoFQ4ODuZd-jctmEbumF-HqM"  # Replace with actual key

# @app.route("/chatbot", methods=["POST"])
# def chatbot():
#     query = request.json.get("query")
#     if not query:
#         return jsonify({"error": "Query is required"}), 400
    
#     prompt = f"""
# You are an assistant that helps users write Selenium action scripts for web testing. Each script should:
# - Be a Python function named after the action (e.g., fill_username).
# - Take a WebDriver instance from `selenium.webdriver.remote.webdriver` as the first parameter.
# - Accept additional parameters as needed (e.g., username, xpath).
# - Return a dictionary with 'status', 'message', and 'interacted_elements' keys. The 'interacted_elements' key should contain a list of XPaths of the elements interacted with during the script's execution.

# Here are two sample scripts for context:

# 1. fill_username.py:
# from selenium.webdriver.remote.webdriver import WebDriver
# from typing import Dict

# def fill_username(driver: WebDriver, username: str, xpath: str = "//input[@type='text']") -> Dict[str, any]:
#     try:
#         username_field = driver.find_element("xpath", xpath)
#         username_field.clear()
#         username_field.send_keys(username)
#         return {{"status": "success", "message": "Username field filled", "interacted_elements": [xpath]}}
#     except Exception as e:
#         return {{"status": "error", "message": str(e), "interacted_elements": []}}

# 2. add_rand_ele.py:
# import random
# import time
# from selenium.webdriver.remote.webdriver import WebDriver
# from typing import Dict

# def add_rand_ele(driver: WebDriver, grid_xpath: str = "//input[@type='text']") -> Dict[str, any]:
#     try:
#         child_xpath = grid_xpath.rstrip("/") + "/div"
#         child_divs = driver.find_elements("xpath", child_xpath)
#         if not child_divs:
#             return {{"status": "error", "message": "No child divs found", "interacted_elements": []}}
#         random_index = random.randint(0, len(child_divs) - 1)
#         selected_div = child_divs[random_index]
#         selected_div.click()
#         # return {{"status": "success", "message": f"Clicked div at index {{random_index + 1}} out of {{len(child_divs)}}", "interacted_elements": [child_xpath + f"[1]"]}}
#     except Exception as e:
#         return {{"status": "error", "message": str(e), "interacted_elements": []}}

# Now, generate a script based on this query: {query}
# """
    
#     response = requests.post(
#         "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=" + GEMINI_API_KEY,
#         headers={"Content-Type": "application/json"},
#         json={"contents": [{"parts": [{"text": prompt}]}]}
#     )
    
#     if response.status_code == 200:
#         generated_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
#         return jsonify({"response": generated_text})
#     else:
#         return jsonify({"error": "Failed to get response from Gemini API"}), 500

# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5000)
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify, render_template, Response
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager  # Added for automatic ChromeDriver management
import os
import importlib.util
import sys
from pathlib import Path
import inspect
import json
import time
import threading
import requests
import traceback

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Selenium WebDriver setup
def get_driver():
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

# Directory for action scripts
ACTIONS_DIR = Path("actions")
ACTIONS_DIR.mkdir(exist_ok=True)

# Helper function to extract parameter names and types from action script
def get_action_params(action_name):
    script_path = ACTIONS_DIR / f"{action_name}.py"
    if not script_path.exists():
        return {}
    spec = importlib.util.spec_from_file_location(action_name, script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[action_name] = module
    spec.loader.exec_module(module)
    action_func = getattr(module, action_name, None)
    if action_func is None:
        return {}
    sig = inspect.signature(action_func)
    params = {}
    for param in sig.parameters.values():
        param_type = param.annotation.__name__ if param.annotation != inspect._empty else "str"
        if param_type in ["str", "int", "float"]:
            params[param.name] = param_type
    return params

# Validate Python script for allowed modules and functions
def validate_script(script_content):
    try:
        return True, "Script validated successfully"
    except SyntaxError:
        return False, "Invalid Python syntax"

# Helper function to wait until page is fully loaded
def wait_until_page_fully_loaded(driver, timeout=10):
    try:
        end_time = time.time() + timeout
        while time.time() < end_time:
            ready_state = driver.execute_script("return document.readyState")
            if ready_state == "complete":
                return {"status": "success", "message": "Page fully loaded"}
            time.sleep(0.5)
        return {"status": "error", "message": "Timed out waiting for page to load"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Helper function to execute an action script
def execute_action(action_name, parameters, driver):
    try:
        script_path = ACTIONS_DIR / f"{action_name}.py"
        if not script_path.exists():
            return {"error": f"Action script {action_name}.py not found"}
        
        wait_until_page_fully_loaded(driver, 20)
        spec = importlib.util.spec_from_file_location(action_name, script_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[action_name] = module
        spec.loader.exec_module(module)
        time.sleep(5)
        
        action_func = getattr(module, action_name, None)
        if not action_func:
            return {"error": f"Function {action_name} not found in {action_name}.py"}
        
        result = action_func(driver, **parameters)
        print(result)
        return {"status": result["status"], "result": result, "interacted_elements": result.get("interacted_elements", [])}
    except Exception as e:
        return {"error": str(e)}

# Function to count elements on a page
def count_elements(driver, url):
    driver.get(url)
    wait_until_page_fully_loaded(driver)
    buttons = driver.find_elements(By.TAG_NAME, "button")
    inputs = driver.find_elements(By.TAG_NAME, "input")
    links = driver.find_elements(By.TAG_NAME, "a")
    return {
        "buttons": len(buttons),
        "inputs": len(inputs),
        "links": len(links)
    }

# Function to run the entire test case
def run_testcase(testcase_data, driver, testcase_id):
    actions = testcase_data.get("actions", [])
    if not actions:
        result = {"message": "No actions to run", "status": "skipped", "results": [], "timestamp": int(time.time() * 1000)}
        db.collection("test_results").document(testcase_id).collection("runs").document(str(int(time.time() * 1000))).set(result)
        return result
    
    results = []
    driver.get(testcase_data.get("proj_url"))
    run_id = str(int(time.time() * 1000))
    
    # Set initial "running" status
    db.collection("test_results").document(testcase_id).collection("runs").document(run_id).set({"status": "running", "results": [], "timestamp": int(time.time() * 1000)})
    
    for action_item in actions:
        action_id = action_item.get("action_id")
        instance_id = action_item.get("instance_id")
        parameters = action_item.get("parameters")
        
        action_doc = db.collection("actions").document(action_id).get()
        if not action_doc.exists:
            action_result = {
                "action_id": action_id,
                "instance_id": instance_id,
                "name": "Unknown",
                "status": "error",
                "details": {"error": "Action not found"}
            }
            results.append(action_result)
            db.collection("test_results").document(testcase_id).collection("runs").document(run_id).set({"status": "running", "results": results, "timestamp": int(time.time() * 1000)}, merge=True)
            continue
        
        action_name = action_doc.to_dict().get("script_file").split(".")[0]
        result = execute_action(action_name, parameters, driver)
        action_result = {
            "action_id": action_id,
            "instance_id": instance_id,
            "name": action_name,
            "status": "passed" if "error" not in result else "failed",
            "details": result.get("result", result.get("error", "No details")),
            "interacted_elements": result.get("interacted_elements", [])
        }
        results.append(action_result)
        # Update Firestore in real-time with status
        db.collection("test_results").document(testcase_id).collection("runs").document(run_id).set({"status": "running", "results": results, "timestamp": int(time.time() * 1000)}, merge=True)
    
    # Determine final status
    try:
        success_element = driver.find_element(By.XPATH, "//*[contains(text(), 'success')]")
        overall_status = "passed" if success_element else "failed"
    except:
        overall_status = "failed" if any(r["status"] == "error" for r in results) else "passed"
    
    final_result = {"message": "Testcase executed", "status": overall_status, "results": results, "timestamp": int(time.time() * 1000)}
    db.collection("test_results").document(testcase_id).collection("runs").document(run_id).set(final_result)
    return final_result

# Fetch past test results
@app.route("/past-results/<testcase_id>", methods=["GET"])
def get_past_results(testcase_id):
    testcase = db.collection("testcases").document(testcase_id).get()
    if not testcase.exists:
        return jsonify({"error": "Testcase not found"}), 404
    
    runs_ref = db.collection("test_results").document(testcase_id).collection("runs")
    past_results = [doc.to_dict() for doc in runs_ref.stream()]
    past_results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)  # Sort by timestamp, newest first
    return jsonify(past_results)

# Render past results page
@app.route("/past-results/<proj_id>/<testcase_id>")
def past_results(proj_id, testcase_id):
    project = db.collection("projects").document(proj_id).get()
    if not project.exists:
        return jsonify({"error": "Project not found"}), 404
    testcase = db.collection("testcases").document(testcase_id).get()
    if not testcase.exists or testcase.to_dict().get("proj_id") != proj_id:
        return jsonify({"error": "Testcase not found or does not belong to project"}), 404
    return render_template("past_results.html", proj_id=proj_id, testcase_id=testcase_id, testcase_name=testcase.to_dict().get("name"))

# Upload new action
@app.route("/addaction/", methods=["POST"])
def add_action():
    action_name = request.form.get("name")
    script_file = request.files.get("script")

    if not (script_file and action_name):
        return jsonify({"error": "Script file and action name are required"}), 400
    
    script_content = script_file.read().decode('utf-8')
    is_valid, message = validate_script(script_content)
    if not is_valid:
        return jsonify({"error": message}), 400
    
    filename = f"{action_name}.py"
    file_path = ACTIONS_DIR / filename
    with open(file_path, "w") as file:
        file.write(script_content)
    
    if not file_path.exists():
        return jsonify({"error": "Failed to save action file"}), 500
    
    parameters_types = get_action_params(action_name)
    if not parameters_types:
        return jsonify({"error": "No valid action function found or failed to extract parameters"}), 400
    
    action_id = db.collection("actions").document().id
    db.collection("actions").document(action_id).set({
        "action_name": action_name,
        "script_file": filename,
        "parameters": parameters_types
    })
    
    return jsonify({
        "message": "Action uploaded successfully",
        "action_id": action_id,
        "action_name": action_name
    })

# View action details
@app.route("/dashboard/<proj_id>/<testcase_id>/<action_id>", methods=["GET"])
def view_action(proj_id, testcase_id, action_id):
    project = db.collection("projects").document(proj_id).get()
    if not project.exists:
        return jsonify({"error": "Project not found"}), 404
    
    testcase = db.collection("testcases").document(testcase_id).get()
    if not testcase.exists or testcase.to_dict().get("proj_id") != proj_id:
        return jsonify({"error": "Testcase not found or does not belong to project"}), 404
    
    action_ref = db.collection("actions").document(action_id).get()
    if not action_ref.exists:
        return jsonify({"error": "Action not found"}), 404
    
    action_data = action_ref.to_dict()
    return render_template(
        "action_details.html",
        proj_id=proj_id,
        testcase_id=testcase_id,
        action_id=action_id,
        action_name=action_data.get("action_name"),
        script_file=action_data.get("script_file"),
        parameters=action_data.get("parameters", {})
    )

# Project management endpoints
@app.route("/dashboard/", methods=["GET", "POST"])
def dashboard():
    if request.method == "GET":
        projects_ref = db.collection("projects")
        return render_template("projects.html", projects=[
            {"id": doc.id, "name": doc.to_dict().get("name")} for doc in projects_ref.stream()
        ])
    
    elif request.method == "POST":
        data = request.get_json()
        action = data.get("action")
        
        if action == "add_project":
            name = data.get("name")
            if not name:
                return jsonify({"error": "Project name is required"}), 400
            existing = db.collection("projects").where("name", "==", name).stream()
            for doc in existing:
                return jsonify({"message": "Project already exists", "proj_id": doc.id})
            proj_id = db.collection("projects").document().id
            db.collection("projects").document(proj_id).set({"name": name})
            return jsonify({"message": "Project created", "proj_id": proj_id})
        
        elif action == "remove_project":
            proj_id = data.get("proj_id")
            if not proj_id:
                return jsonify({"error": "proj_id is required"}), 400
            project = db.collection("projects").document(proj_id).get()
            if not project.exists:
                return jsonify({"error": "Project not found"}), 404
            db.collection("projects").document(proj_id).delete()
            testcases = db.collection("testcases").where("proj_id", "==", proj_id).stream()
            for tc in testcases:
                db.collection("test_results").document(tc.id).delete()  # Clean up results
                db.collection("testcases").document(tc.id).delete()
            return jsonify({"message": "Project removed"})
        
        elif action == "select_project":
            proj_id = data.get("proj_id")
            if not proj_id:
                return jsonify({"error": "proj_id is required"}), 400
            project = db.collection("projects").document(proj_id).get()
            if not project.exists:
                return jsonify({"error": "Project not found"}), 404
            return jsonify({"proj_id": proj_id, "name": project.to_dict().get("name")})
        
        return jsonify({"error": "Invalid action"}), 400

# Test case management endpoints
@app.route("/dashboard/<proj_id>", methods=["GET", "POST"])
def project_dashboard(proj_id):
    project = db.collection("projects").document(proj_id).get()
    if not project.exists:
        return jsonify({"error": "Project not found"}), 404
    
    if request.method == "GET":
        testcases_ref = db.collection("testcases").where("proj_id", "==", proj_id)
        testcases = [
            {"id": doc.id, "name": doc.to_dict().get("name"), "proj_url": doc.to_dict().get("proj_url")}
            for doc in testcases_ref.stream()
        ]
        return render_template("testcases.html", proj_id=proj_id, proj_name=project.to_dict().get("name"), testcases=testcases)    
    elif request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        action = data.get("action")
        
        if action == "add_testcase":
            name = data.get("name")
            proj_url = data.get("proj_url")
            if not (name and proj_url):
                return jsonify({"error": "name and proj_url are required"}), 400
            existing = db.collection("testcases").where("proj_id", "==", proj_id).where("name", "==", name).stream()
            for doc in existing:
                return jsonify({"error": "Testcase name already exists in this project", "testcase_id": doc.id}), 400
            testcase_id = db.collection("testcases").document().id
            db.collection("testcases").document(testcase_id).set({
                "proj_id": proj_id,
                "name": name,
                "proj_url": proj_url,
                "actions": []
            })
            return jsonify({"message": "Testcase created", "testcase_id": testcase_id})
        
        elif action == "remove_testcase":
            testcase_id = data.get("testcase_id")
            if not testcase_id:
                return jsonify({"error": "testcase_id is required"}), 400
            testcase = db.collection("testcases").document(testcase_id).get()
            if not testcase.exists or testcase.to_dict().get("proj_id") != proj_id:
                return jsonify({"error": "Testcase not found or does not belong to project"}), 404
            db.collection("test_results").document(testcase_id).delete()  # Clean up results
            db.collection("testcases").document(testcase_id).delete()
            return jsonify({"message": "Testcase removed"})
        
        elif action == "select_testcase":
            testcase_id = data.get("testcase_id")
            if not testcase_id:
                return jsonify({"error": "testcase_id is required"}), 400
            testcase = db.collection("testcases").document(testcase_id).get()
            if not testcase.exists or testcase.to_dict().get("proj_id") != proj_id:
                return jsonify({"error": "Testcase not found or does not belong to project"}), 404
            return jsonify({"testcase_id": testcase_id, "name": testcase.to_dict().get("name")})
        
        return jsonify({"error": "Invalid action"}), 400

# Run test case in a background thread
@app.route("/run-testcase/<testcase_id>", methods=["POST"])
def run_testcase_endpoint(testcase_id):
    testcase = db.collection("testcases").document(testcase_id).get()
    if not testcase.exists:
        return jsonify({"error": "Testcase not found"}), 404
    
    # Initialize the result in Firestore
    db.collection("test_results").document(testcase_id).set({"status": "running", "results": []})
    
    def run_testcase_task():
        driver = get_driver()
        try:
            result = run_testcase(testcase.to_dict(), driver, testcase_id)
        finally:
            driver.quit()
    
    thread = threading.Thread(target=run_testcase_task)
    thread.start()
    return jsonify({"message": "Test case running", "testcase_id": testcase_id})

# Fetch test case results
@app.route("/get-results/<testcase_id>", methods=["GET"])
def get_results(testcase_id):
    result_doc = db.collection("test_results").document(testcase_id).get()
    if not result_doc.exists:
        return jsonify({"status": "pending"})
    return jsonify(result_doc.to_dict())

# Render results page
@app.route("/results/<proj_id>/<testcase_id>")
def results(proj_id, testcase_id):
    project = db.collection("projects").document(proj_id).get()
    if not project.exists:
        return jsonify({"error": "Project not found"}), 404
    testcase = db.collection("testcases").document(testcase_id).get()
    if not testcase.exists or testcase.to_dict().get("proj_id") != proj_id:
        return jsonify({"error": "Testcase not found or does not belong to project"}), 404
    return render_template("results.html", proj_id=proj_id, testcase_id=testcase_id, testcase_name=testcase.to_dict().get("name"))

# Elements Summary Report for a single test case
@app.route("/elements-summary/<testcase_id>", methods=["GET"])
def elements_summary(testcase_id):
    testcase = db.collection("testcases").document(testcase_id).get()
    if not testcase.exists:
        return jsonify({"error": "Testcase not found"}), 404
    url = testcase.to_dict().get("proj_url")
    
    # Count total elements using Selenium
    driver = get_driver()
    total_elements = count_elements(driver, url)
    driver.quit()
    
    # Fetch all passed test runs for this testcase
    runs_ref = db.collection("test_results").document(testcase_id).collection("runs").where("status", "==", "passed").stream()
    tested_elements = set()
    for run in runs_ref:
        run_data = run.to_dict()
        for result in run_data.get("results", []):
            for elem in result.get("interacted_elements", []):
                tested_elements.add(elem)
    
    # Calculate tested counts
    tested_buttons = sum(1 for e in tested_elements if "button" in e.lower())
    tested_inputs = sum(1 for e in tested_elements if "input" in e.lower())
    tested_links = sum(1 for e in tested_elements if "/A[" in e)
    
    # Calculate percentages
    total_all = total_elements["buttons"] + total_elements["inputs"] + total_elements["links"]
    tested_all = tested_buttons + tested_inputs + tested_links
    coverage_percentage = (tested_all / total_all * 100) if total_all > 0 else 0
    button_percentage = (tested_buttons / total_elements["buttons"] * 100) if total_elements["buttons"] > 0 else 0
    input_percentage = (tested_inputs / total_elements["inputs"] * 100) if total_elements["inputs"] > 0 else 0
    link_percentage = (tested_links / total_elements["links"] * 100) if total_elements["links"] > 0 else 0
    
    report_data = {
        "url": url,
        "testcase_name": testcase.to_dict().get("name"),
        "elements": [
            {"type": "Buttons", "total": total_elements["buttons"], "tested": tested_buttons, "percentage": round(button_percentage, 2)},
            {"type": "Inputs", "total": total_elements["inputs"], "tested": tested_inputs, "percentage": round(input_percentage, 2)},
            {"type": "Links", "total": total_elements["links"], "tested": tested_links, "percentage": round(link_percentage, 2)}
        ],
        "summary": {
            "total_elements": total_all,
            "tested_elements": tested_all,
            "coverage_percentage": round(coverage_percentage, 2)
        }
    }
    return render_template("elements_summary.html", report=report_data)

# Project-level Elements Summary Report
@app.route("/project-elements-summary/<proj_id>", methods=["GET"])
def project_elements_summary(proj_id):
    project = db.collection("projects").document(proj_id).get()
    if not project.exists:
        return jsonify({"error": "Project not found"}), 404
    
    # Fetch all test cases for the project
    testcases_ref = db.collection("testcases").where("proj_id", "==", proj_id).stream()
    testcases = [(doc.id, doc.to_dict()) for doc in testcases_ref]
    
    if not testcases:
        return jsonify({"error": "No test cases found for this project"}), 404
    
    # Group test cases by URL
    url_to_testcases = {}
    for testcase_id, testcase_data in testcases:
        url = testcase_data.get("proj_url")
        if url not in url_to_testcases:
            url_to_testcases[url] = []
        url_to_testcases[url].append((testcase_id, testcase_data))
    
    driver = get_driver()
    reports = []
    project_summary = {"buttons": {"total": 0, "tested": 0}, "inputs": {"total": 0, "tested": 0}, "links": {"total": 0, "tested": 0}}
    
    # Process each URL
    for url, testcase_list in url_to_testcases.items():
        # Count total elements for this URL
        total_elements = count_elements(driver, url)
        
        # Aggregate tested elements across all test cases for this URL
        tested_elements = set()
        for testcase_id, _ in testcase_list:
            runs_ref = db.collection("test_results").document(testcase_id).collection("runs").where("status", "==", "passed").stream()
            for run in runs_ref:
                run_data = run.to_dict()
                for result in run_data.get("results", []):
                    for elem in result.get("interacted_elements", []):
                        tested_elements.add(elem)
        
        # Calculate tested counts
        tested_buttons = sum(1 for e in tested_elements if "button" in e.lower())
        tested_inputs = sum(1 for e in tested_elements if "input" in e.lower())
        tested_links = sum(1 for e in tested_elements if "/A[" in e)
        
        # Calculate percentages
        total_all = total_elements["buttons"] + total_elements["inputs"] + total_elements["links"]
        tested_all = tested_buttons + tested_inputs + tested_links
        coverage_percentage = (tested_all / total_all * 100) if total_all > 0 else 0
        button_percentage = (tested_buttons / total_elements["buttons"] * 100) if total_elements["buttons"] > 0 else 0
        input_percentage = (tested_inputs / total_elements["inputs"] * 100) if total_elements["inputs"] > 0 else 0
        link_percentage = (tested_links / total_elements["links"] * 100) if total_elements["links"] > 0 else 0
        
        # Update project summary
        project_summary["buttons"]["total"] += total_elements["buttons"]
        project_summary["buttons"]["tested"] += tested_buttons
        project_summary["inputs"]["total"] += total_elements["inputs"]
        project_summary["inputs"]["tested"] += tested_inputs
        project_summary["links"]["total"] += total_elements["links"]
        project_summary["links"]["tested"] += tested_links
        
        report_data = {
            "url": url,
            "testcases": [{"id": tc_id, "name": tc_data.get("name")} for tc_id, tc_data in testcase_list],
            "elements": [
                {"type": "Buttons", "total": total_elements["buttons"], "tested": tested_buttons, "percentage": round(button_percentage, 2)},
                {"type": "Inputs", "total": total_elements["inputs"], "tested": tested_inputs, "percentage": round(input_percentage, 2)},
                {"type": "Links", "total": total_elements["links"], "tested": tested_links, "percentage": round(link_percentage, 2)}
            ],
            "summary": {
                "total_elements": total_all,
                "tested_elements": tested_all,
                "coverage_percentage": round(coverage_percentage, 2)
            }
        }
        reports.append(report_data)
    
    driver.quit()
    
    # Calculate project-wide summary statistics
    project_total = project_summary["buttons"]["total"] + project_summary["inputs"]["total"] + project_summary["links"]["total"]
    project_tested = project_summary["buttons"]["tested"] + project_summary["inputs"]["tested"] + project_summary["links"]["tested"]
    project_coverage = (project_tested / project_total * 100) if project_total > 0 else 0
    project_summary["total_elements"] = project_total
    project_summary["tested_elements"] = project_tested
    project_summary["coverage_percentage"] = round(project_coverage, 2)
    project_summary["buttons"]["percentage"] = round((project_summary["buttons"]["tested"] / project_summary["buttons"]["total"] * 100) if project_summary["buttons"]["total"] > 0 else 0, 2)
    project_summary["inputs"]["percentage"] = round((project_summary["inputs"]["tested"] / project_summary["inputs"]["total"] * 100) if project_summary["inputs"]["total"] > 0 else 0, 2)
    project_summary["links"]["percentage"] = round((project_summary["links"]["tested"] / project_summary["links"]["total"] * 100) if project_summary["links"]["total"] > 0 else 0, 2)
    
    return render_template("project_elements_summary.html", project_name=project.to_dict().get("name"), reports=reports, project_summary=project_summary)

@app.route("/dashboard/<proj_id>/<testcase_id>", methods=["GET", "POST"])
def testcase_dashboard(proj_id, testcase_id):
    project = db.collection("projects").document(proj_id).get()
    if not project.exists:
        return jsonify({"error": "Project not found"}), 404
    testcase = db.collection("testcases").document(testcase_id).get()
    if not testcase.exists or testcase.to_dict().get("proj_id") != proj_id:
        return jsonify({"error": "Testcase not found or does not belong to project"}), 404
    
    if request.method == "GET":
        testcase_data = testcase.to_dict()
        actions_ref = db.collection("actions")
        actions = {  
            doc.id: {"id": doc.id, "name": doc.to_dict().get("action_name"), "parameters": doc.to_dict().get("parameters", {})}
            for doc in actions_ref.stream()
        }
        res = testcase_data.get("actions", [])
        for action in res:
            action["name"] = actions[action['action_id']]['name']
        return render_template(
            "testcase_details.html",
            proj_id=proj_id,
            testcase_id=testcase_id,
            testcase_name=testcase_data.get("name"),
            proj_url=testcase_data.get("proj_url"),
            actions=testcase_data.get("actions", []),
            available_actions=list(actions.values())
        )
    
    elif request.method == "POST":
        data = request.get_json(silent=True)
        if data:
            action = data.get("action")
            
            if action == "add_action":
                action_id = data.get("action_id")
                parameters = data.get("parameters", {})
                if not action_id:
                    return jsonify({"error": "action_id is required"}), 400
                
                action_doc = db.collection("actions").document(action_id).get()
                if not action_doc.exists:
                    return jsonify({"error": "Action not found"}), 404
                
                expected_params = action_doc.to_dict().get("parameters", {})
                for param in expected_params.keys():
                    if param not in parameters:
                        return jsonify({"error": f"Missing parameter: {param}"}), 400
                    if expected_params[param] == "int":
                        try:
                            parameters[param] = int(parameters[param])
                        except ValueError:
                            return jsonify({"error": f"Parameter {param} must be an integer"}), 400
                    elif expected_params[param] == "float":
                        try:
                            parameters[param] = float(parameters[param])
                        except ValueError:
                            return jsonify({"error": f"Parameter {param} must be a float"}), 400
                    elif expected_params[param] != "str":
                        return jsonify({"error": f"Unsupported type {expected_params[param]} for parameter {param}"}), 400
                
                testcase_ref = db.collection("testcases").document(testcase_id)
                testcase_ref.update({
                    "actions": firestore.ArrayUnion([{
                        "action_id": action_id,
                        "parameters": parameters
                    }])
                })
                return jsonify({"message": "Action added"})
            
            elif action == "update_actions":
                new_actions = data.get("actions", [])
                if not isinstance(new_actions, list):
                    return jsonify({"error": "actions must be a list"}), 400
                for action_item in new_actions:
                    if not isinstance(action_item, dict) or "action_id" not in action_item or "parameters" not in action_item:
                        return jsonify({"error": "Each action must have action_id and parameters"}), 400
                    action_doc = db.collection("actions").document(action_item["action_id"]).get()
                    if not action_doc.exists:
                        return jsonify({"error": f"Action {action_item['action_id']} not found"}), 404
                    expected_params = action_doc.to_dict().get("parameters", {})
                    for param in expected_params.keys():
                        if param not in action_item["parameters"]:
                            return jsonify({"error": f"Missing parameter: {param} for action {action_item['action_id']}"}), 400
                        if expected_params[param] == "int":
                            try:
                                action_item["parameters"][param] = int(action_item["parameters"][param])
                            except ValueError:
                                return jsonify({"error": f"Parameter {param} must be an integer for action {action_item['action_id']}"}), 400
                        elif expected_params[param] == "float":
                            try:
                                action_item["parameters"][param] = float(action_item["parameters"][param])
                            except ValueError:
                                return jsonify({"error": f"Parameter {param} must be a float for action {action_item['action_id']}"}), 400
                        elif expected_params[param] != "str":
                            return jsonify({"error": f"Unsupported type {expected_params[param]} for parameter {param} for action {action_item['action_id']}"}), 400
                testcase_ref = db.collection("testcases").document(testcase_id)
                testcase_ref.update({"actions": new_actions})
                return jsonify({"message": "Testcase actions updated"})
            
            elif action == "run_testcase":
                return run_testcase_endpoint(testcase_id)
        
        return jsonify({"error": "Invalid action or request format"}), 400

@app.route("/dashboard/<proj_id>/testcases", methods=["GET"])
def view_testcases(proj_id):
    project = db.collection("projects").document(proj_id).get()
    if not project.exists:
        return jsonify({"error": "Project not found"}), 404
    testcases = db.collection("testcases").where("proj_id", "==", proj_id).stream()
    testcase_list = [{"id": tc.id, "name": tc.to_dict().get("name"), "proj_url": tc.to_dict().get("proj_url")} for tc in testcases]
    return render_template("testcases.html", proj_id=proj_id, testcases=testcase_list)

@app.route("/newaction/", methods=["GET"])
def new_action():
    proj_id = request.args.get("proj_id")
    testcase_id = request.args.get("testcase_id")
    return render_template("actions_view.html", proj_id=proj_id, testcase_id=testcase_id)

@app.route('/proxy')
def proxy():
    url = request.args.get('url')
    if not url:
        return "Missing 'url' parameter", 400
    print("Fetching URL:", url)
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        response = session.get(url, allow_redirects=True)
        content_type = response.headers.get('Content-Type', 'text/html')
        return Response(response.content, content_type=content_type)
    except Exception as e:
        print("Error:", str(e))
        traceback.print_exc()
        return f"Error fetching content: {str(e)}", 500

@app.route('/capture_xpath', methods=['POST'])
def capture_xpath():
    data = request.get_json()
    xpath = data.get('xpath')
    print(f"Captured XPath: {xpath}")
    return Response("Received XPath", status=200, mimetype='text/plain')

# Chatbot integration
GEMINI_API_KEY = "AIzaSyBpsEsyY3sxoFQ4ODuZd-jctmEbumF-HqM"  # Replace with actual key

@app.route("/chatbot", methods=["POST"])
def chatbot():
    query = request.json.get("query")
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    prompt = f"""
You are an assistant that helps users write Selenium action scripts for web testing. Each script should:
- Be a Python function named after the action (e.g., fill_username).
- Take a WebDriver instance from `selenium.webdriver.remote.webdriver` as the first parameter.
- Accept additional parameters as needed (e.g., username, xpath).
- Return a dictionary with 'status', 'message', and 'interacted_elements' keys. The 'interacted_elements' key should contain a list of XPaths of the elements interacted with during the script's execution.

Here are two sample scripts for context:

1. fill_username.py:
from selenium.webdriver.remote.webdriver import WebDriver
from typing import Dict

def fill_username(driver: WebDriver, username: str, xpath: str = "//input[@type='text']") -> Dict[str, any]:
    try:
        username_field = driver.find_element("xpath", xpath)
        username_field.clear()
        username_field.send_keys(username)
        return {{"status": "success", "message": "Username field filled", "interacted_elements": [xpath]}}
    except Exception as e:
        return {{"status": "error", "message": str(e), "interacted_elements": []}}

2. add_rand_ele.py:
import random
import time
from selenium.webdriver.remote.webdriver import WebDriver
from typing import Dict

def add_rand_ele(driver: WebDriver, grid_xpath: str = "//input[@type='text']") -> Dict[str, any]:
    try:
        child_xpath = grid_xpath.rstrip("/") + "/div"
        child_divs = driver.find_elements("xpath", child_xpath)
        if not child_divs:
            return {{"status": "error", "message": "No child divs found", "interacted_elements": []}}
        random_index = random.randint(0, len(child_divs) - 1)
        selected_div = child_divs[random_index]
        selected_div.click()
        return {{"status": "success", "message": f"Clicked div at index {{random_index + 1}} out of {{len(child_divs)}}", "interacted_elements": [child_xpath + f"[{'random_index + 1'}]"]}}
    except Exception as e:
        return {{"status": "error", "message": str(e), "interacted_elements": []}}

Now, generate a script based on this query: {query}
"""
    
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=" + GEMINI_API_KEY,
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]}
    )
    
    if response.status_code == 200:
        generated_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return jsonify({"response": generated_text})
    else:
        return jsonify({"error": "Failed to get response from Gemini API"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)