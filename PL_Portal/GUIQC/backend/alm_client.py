import os
import requests
import json
from typing import Dict, List, Any, Optional

class ALMClient:
    def __init__(self, base_url: str, domain: str, project: str):
        self.base_url = base_url.rstrip('/')
        self.domain = domain
        self.project = project
        self.cookies = {}
        self.session = requests.Session()
        # Headers for ALM REST API
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def authenticate(self, username, password) -> bool:
        """
        Authenticates with ALM using Basic Auth or LWSSO.
        Stores cookies on success.
        """
        auth_url = f"{self.base_url}/qcbin/authentication-point/authenticate"
        
        try:
            # First request to authenticate
            response = self.session.post(auth_url, auth=(username, password))
            
            if response.status_code == 200:
                print("Authentication successful.")
                
                # Create site session (required for ALM 12.x+)
                session_url = f"{self.base_url}/qcbin/rest/site-session"
                session_response = self.session.post(session_url)
                
                if session_response.status_code in [200, 201]:
                    print("Site session created.")
                    return True
                else:
                    print(f"Site session creation failed: {session_response.status_code}")
                    # Continue anyway as some ALM versions might not need this
                    return True
            else:
                print(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def get_dashboard_stats(self, folder_id: int) -> Dict[str, Any]:
        """
        Aggregates statistics for a specific test set folder.
        Recursive with Failure Collection.
        """
        # 1. Fetch the folder details to get its name
        folder_details = self._get_folder_details(folder_id)
        if not folder_details:
             return {"error": f"Folder {folder_id} not found"}

        folder_name = folder_details.get('name', 'Unknown')
        
        # 2. Get children folders
        children_structure = self._get_folder_children(folder_id)
        
        # Initialize stats
        stats = {
            "folder_id": folder_id,
            "folder_name": folder_name,
            "summary": {
                "total": 0,
                "executed": 0,
                "passed": 0,
                "failed": 0,
                "not_executed": 0,
                "execution_percentage": 0.0
            },
            "failed_tests": [],
            "children": []
        }
        
        # Helper to process test instances
        def process_instances(instances_list, current_stats):
            for instance in instances_list:
                status = instance.get('status', 'N/A')
                is_executed = status in ['Passed', 'Failed', 'Blocked', 'Warning']
                
                current_stats['summary']['total'] += 1
                if is_executed:
                    current_stats['summary']['executed'] += 1
                    
                    if status == 'Passed':
                        current_stats['summary']['passed'] += 1
                    elif status in ['Failed', 'Blocked']:
                        current_stats['summary']['failed'] += 1
                        # Collect failed test
                        if len(current_stats['failed_tests']) < 50: # Limit size
                            current_stats['failed_tests'].append({
                                "id": instance.get('id'),
                                "name": instance.get('name'),
                                "status": status,
                                "owner": instance.get('owner'),
                                "exec_date": instance.get('exec_date'),
                                "path": folder_name # Simple path info
                            })
                else:
                    current_stats['summary']['not_executed'] += 1

        # Check if this is a leaf folder (has no sub-folders)
        is_leaf_folder = len(children_structure) == 0
        
        # Handle Test Sets (Mixed Content or Leaf)
        # Always check for test sets in the current folder, regardless of children
        # This fixes Mixed Content issues
        current_folder_test_sets = self._get_test_sets_in_folder(folder_id)
        for test_set in current_folder_test_sets:
            instances = self._get_test_instances_in_set(test_set.get('id'))
            process_instances(instances, stats)

        # Handle Sub-Folders (Recursion)
        for child in children_structure:
            child_id = child['id']
            child_stats = self.get_dashboard_stats(int(child_id))
            
            if "error" not in child_stats:
                # Aggregate summary
                stats['summary']['total'] += child_stats['summary']['total']
                stats['summary']['executed'] += child_stats['summary']['executed']
                stats['summary']['passed'] += child_stats['summary']['passed']
                stats['summary']['failed'] += child_stats['summary']['failed']
                stats['summary']['not_executed'] += child_stats['summary']['not_executed']
                
                # Aggregate Failed Tests (up to limit)
                remaining_slots = 50 - len(stats['failed_tests'])
                if remaining_slots > 0:
                    stats['failed_tests'].extend(child_stats['failed_tests'][:remaining_slots])

                # Add child to children list for cards
                stats['children'].append({
                    "id": child_id,
                    "name": child['name'],
                    "type": "folder",
                    "executed": child_stats['summary']['executed'],
                    "passed": child_stats['summary']['passed'],
                    "failed": child_stats['summary']['failed'],
                    "not_executed": child_stats['summary']['not_executed'],
                    "total": child_stats['summary']['total']
                })
        
        # Calculate percentage
        if stats['summary']['total'] > 0:
            stats['summary']['execution_percentage'] = round((stats['summary']['executed'] / stats['summary']['total']) * 100, 1)
        
        return stats
    
    def _get_test_sets_in_folder(self, folder_id: int) -> List[Dict]:
        """Get all test sets directly in this folder"""
        url = f"{self.base_url}/qcbin/rest/domains/{self.domain}/projects/{self.project}/test-sets"
        params = {
            'query': f"{{parent-id[{folder_id}]}}",
            'fields': 'id,name',
            'page-size': 500
        }
        
        response = self.session.get(url, params=params)
        if response.status_code == 200:
            entities = response.json().get('entities', [])
            result = []
            for e in entities:
                flat = self._flatten_fields(e['Fields'])
                result.append({'id': flat.get('id'), 'name': flat.get('name')})
            return result
        return []
    
    def _get_test_instances_in_set(self, test_set_id: int) -> List[Dict]:
        """Get test instances for a specific test set"""
        url = f"{self.base_url}/qcbin/rest/domains/{self.domain}/projects/{self.project}/test-instances"
        params = {
            'query': f"{{cycle-id[{test_set_id}]}}",
            'page-size': 500
        }
        
        response = self.session.get(url, params=params)
        if response.status_code == 200:
            entities = response.json().get('entities', [])
            
            # DEBUG
            if entities and not os.path.exists("backend/debug_instance.json"):
                 import json
                 try:
                     with open("backend/debug_instance.json", "w") as f:
                         f.write(json.dumps(entities[0], indent=2))
                 except: pass

            result = []
            for e in entities:
                flat = self._flatten_fields(e['Fields'])
                result.append({
                    'id': flat.get('id'),
                    'name': flat.get('name') or flat.get('test-config-name') or 'N/A',
                    'status': flat.get('status'),
                    'owner': flat.get('owner'),
                    'exec_date': flat.get('exec-date')
                })
            return result
        return []



    
    def get_pl_device_folders(self) -> List[Dict]:
        """
        Searches for all folders starting with 'PL' (Devices).
        Restricted to Root Level (Parent ID 0) as per user request.
        """
        url = f"{self.base_url}/qcbin/rest/domains/{self.domain}/projects/{self.project}/test-set-folders"
        # Query: name starts with PL* AND parent-id is 0 (Root)
        query = "{name['PL*']; parent-id[0]}"
        params = {
            'query': query,
            'fields': 'id,name,parent-id',
            'page-size': 2000
        }
        
        try:
            response = self.session.get(url, params=params)
            device_folders = []
            
            if response.status_code == 200:
                entities = response.json().get('entities', [])
                for e in entities:
                    flat = self._flatten_fields(e['Fields'])
                    # Simple filter: Ensure name actually starts with PL (case insensitive if needed, but ALM query handles it)
                    name = flat.get('name', '')
                    if name.upper().startswith('PL'):
                        device_folders.append({
                            'id': flat.get('id'),
                            'name': name,
                            'parent_id': flat.get('parent-id'), 
                            'type': 'device'
                        })
                
                # Sort by name
                device_folders.sort(key=lambda x: x['name'])
                return device_folders
            else:
                print(f"Error searching PL folders: {response.text}")
                return []
        except Exception as e:
            print(f"Exception exploring PL folders: {e}")
            return []

    def get_children_folders(self, folder_id: int) -> List[Dict]:
        """
        Public wrapper to get children mapping to 'Version' or 'Sub-Folder'
        """
        children = self._get_folder_children(folder_id)
        # Enrich type
        result = []
        for c in children:
            result.append({
                'id': c['id'],
                'name': c['name'],
                'type': 'version', # Assuming children of PL are versions
                'parent_id': folder_id
            })
        return result

    def _get_folder_details(self, folder_id):
        url = f"{self.base_url}/qcbin/rest/domains/{self.domain}/projects/{self.project}/test-set-folders/{folder_id}"
        res = self.session.get(url)
        if res.status_code == 200:
            data = res.json()
            return {
                "id": folder_id,
                "name": self._flatten_fields(data['Fields']).get('name')
            }
        return None

    def _get_folder_children(self, folder_id):
        """
        Returns a list of immediate child folders.
        """
        # Query test-set-folders where parent-id is folder_id
        url = f"{self.base_url}/qcbin/rest/domains/{self.domain}/projects/{self.project}/test-set-folders"
        query = f"{{parent-id[{folder_id}]}}"
        params = {'query': query, 'fields': 'id,name'}
        
        res = self.session.get(url, params=params)
        children = []
        if res.status_code == 200:
            entities = res.json().get('entities', [])
            for e in entities:
                flat = self._flatten_fields(e['Fields'])
                children.append({
                    "name": flat.get('name'),
                    "type": "folder",
                    "id": flat.get('id')
                })
        return children

    def _flatten_fields(self, fields_list):
        """
        Helper to convert ALM API [{'Name': 'status', 'values': [{'value': 'Passed'}]}] 
        to {'status': 'Passed'}
        """
        result = {}
        for field in fields_list:
            name = field['Name']
            values = field.get('values', [])
            if values:
                result[name] = values[0].get('value')
            else:
                result[name] = None
        return result
