# core/macro_extractor.py
import os
import zipfile
import re
import xml.etree.ElementTree as ET
from io import BytesIO

class MacroExtractor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.macros = []
        self.error = None
        
    def extract_macros(self):
        """Extract VBA macros from Excel files"""
        try:
            # Check if file exists
            if not os.path.exists(self.file_path):
                self.error = f"File not found: {self.file_path}"
                return False
            
            # Check if it's an Excel file with macros (.xlsm)
            extension = os.path.splitext(self.file_path)[1].lower()
            if extension != '.xlsm':
                self.error = f"Not an Excel file with macros (.xlsm): {extension}"
                return False
            
            # Extract macros from the Excel file
            try:
                return self._extract_macros_from_xlsm()
            except Exception as e:
                self.error = f"Failed to extract macros: {str(e)}"
                return False
        except Exception as e:
            self.error = f"Error extracting macros: {str(e)}"
            return False
    
    def _extract_macros_from_xlsm(self):
        """Extract macros from XLSM file (ZIP archive)"""
        try:
            with zipfile.ZipFile(self.file_path, 'r') as z:
                # Look for vbaProject.bin
                if 'xl/vbaProject.bin' not in z.namelist():
                    self.error = "No VBA project found in the file"
                    return False
                
                # Extract module information from the XML files
                vba_modules = self._find_vba_modules(z)
                
                # For each module, extract the code
                for module in vba_modules:
                    module_code = self._extract_module_code(z, module)
                    if module_code:
                        self.macros.append({
                            'name': module['name'],
                            'type': module['type'],
                            'code': module_code
                        })
                
                return len(self.macros) > 0
        except Exception as e:
            self.error = f"Error opening ZIP archive: {str(e)}"
            return False
    
    def _find_vba_modules(self, zip_file):
        """Find VBA modules in the Excel file"""
        modules = []
        
        try:
            # Check if we have the vbaProject.xml file that contains module info
            if 'xl/vbaProject.xml' in zip_file.namelist():
                with zip_file.open('xl/vbaProject.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    
                    # Find modules in the XML
                    for module_elem in root.findall('.//{*}module'):
                        name = module_elem.get('name', 'Unknown')
                        module_type = module_elem.get('type', 'Standard')
                        modules.append({
                            'name': name,
                            'type': module_type
                        })
            
            # If we couldn't find the XML, try to deduce from file structure
            if not modules:
                for filename in zip_file.namelist():
                    if filename.startswith('xl/vba/'):
                        name = os.path.splitext(os.path.basename(filename))[0]
                        modules.append({
                            'name': name,
                            'type': 'Standard'  # Assume standard module
                        })
        except Exception as e:
            print(f"Error finding VBA modules: {str(e)}")
        
        return modules
    
    def _extract_module_code(self, zip_file, module):
        """Extract code from a VBA module"""
        # Note: This is a simplified approach. Advanced macro extraction
        # requires specialized libraries to parse the binary vbaProject.bin
        
        # Try some common paths where code might be stored
        potential_paths = [
            f"xl/vba/{module['name']}.bas",
            f"xl/vba/{module['name']}.cls",
            f"xl/modules/{module['name']}.bas"
        ]
        
        for path in potential_paths:
            if path in zip_file.namelist():
                with zip_file.open(path) as f:
                    return f.read().decode('utf-8', errors='ignore')
        
        # If we couldn't find the module file, try to extract from vbaProject.bin
        # This is a very simplistic approach as proper extraction requires specialized parsing
        try:
            with zip_file.open('xl/vbaProject.bin') as f:
                content = f.read()
                # Look for the module name followed by potential code
                pattern = f"{module['name']}.*?Sub|Function|Property".encode('utf-8')
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    return matches[0].decode('utf-8', errors='ignore')
        except Exception:
            pass
        
        return f"// Code extraction not possible. Module: {module['name']}"
    
    def analyze_macros(self):
        """Analyze the extracted macros to determine their purpose and complexity"""
        for macro in self.macros:
            # Analyze the macro code
            macro_info = self._analyze_macro_code(macro['code'])
            
            # Update the macro with analysis information
            macro.update(macro_info)
        
        return self.macros
    
    def _analyze_macro_code(self, code):
        """Analyze macro code to extract metadata and determine complexity"""
        # Initialize the result
        result = {
            'purpose': 'Unknown',
            'complexity': 0,
            'interacts_with_database': False,
            'interacts_with_external_files': False,
            'handles_events': False,
            'has_user_interface': False
        }
        
        # Convert to lowercase for case-insensitive matching
        code_lower = code.lower()
        
        # Check for database interactions
        if ('adodb' in code_lower or 'connection' in code_lower or 'recordset' in code_lower or 
            'sql' in code_lower or 'query' in code_lower):
            result['interacts_with_database'] = True
            result['complexity'] += 15
        
        # Check for external file interactions
        if ('open' in code_lower and ('for input' in code_lower or 'for output' in code_lower) or
            'filesystemobject' in code_lower or 'createtextfile' in code_lower):
            result['interacts_with_external_files'] = True
            result['complexity'] += 10
        
        # Check for event handlers
        if 'sub worksheet_' in code_lower or 'sub workbook_' in code_lower:
            result['handles_events'] = True
            result['complexity'] += 8
        
        # Check for UI elements
        if ('msgbox' in code_lower or 'inputbox' in code_lower or 'userform' in code_lower or
            'dialog' in code_lower):
            result['has_user_interface'] = True
            result['complexity'] += 12
        
        # Count loops and conditionals
        loop_count = code_lower.count('for ') + code_lower.count('do while') + code_lower.count('do until')
        if_count = code_lower.count('if ') 
        result['complexity'] += (loop_count * 3) + (if_count * 2)
        
        # Determine purpose based on keywords
        if 'report' in code_lower or 'print' in code_lower:
            result['purpose'] = 'Reporting'
        elif 'import' in code_lower or 'export' in code_lower:
            result['purpose'] = 'Data Import/Export'
        elif 'calculate' in code_lower or 'computation' in code_lower:
            result['purpose'] = 'Calculation'
        elif 'format' in code_lower or 'style' in code_lower:
            result['purpose'] = 'Formatting'
        elif result['has_user_interface']:
            result['purpose'] = 'User Interface'
        elif result['interacts_with_database']:
            result['purpose'] = 'Database Interaction'
        
        # Cap complexity at 100
        result['complexity'] = min(100, result['complexity'])
        
        return result
    
    def get_summary(self):
        """Return a summary of the macro analysis"""
        if not self.macros:
            return {
                'macro_count': 0,
                'has_macros': False
            }
        
        total_complexity = sum(macro.get('complexity', 0) for macro in self.macros)
        avg_complexity = total_complexity / len(self.macros) if self.macros else 0
        
        # Categorize macros by purpose
        purposes = {}
        for macro in self.macros:
            purpose = macro.get('purpose', 'Unknown')
            if purpose in purposes:
                purposes[purpose] += 1
            else:
                purposes[purpose] = 1
        
        return {
            'macro_count': len(self.macros),
            'has_macros': len(self.macros) > 0,
            'average_complexity': avg_complexity,
            'total_complexity': total_complexity,
            'purposes': purposes,
            'macros': self.macros  # Include the full macro details
        }