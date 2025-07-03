#!/usr/bin/env python3
"""
Example: Batch process multiple passport images
"""

import requests
import json
import os
import sys
from datetime import datetime
import concurrent.futures
from typing import List, Dict

class BatchProcessor:
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        self.results = []
        
    def process_single_passport(self, image_path: str) -> Dict:
        """Process a single passport image"""
        try:
            with open(image_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.server_url}/extract-file",
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'file': os.path.basename(image_path),
                    'success': result.get('success', False),
                    'data': result.get('data', {}),
                    'accuracy': result.get('accuracy', '0%'),
                    'error': result.get('error')
                }
            else:
                return {
                    'file': os.path.basename(image_path),
                    'success': False,
                    'error': f'HTTP {response.status_code}'
                }
                
        except Exception as e:
            return {
                'file': os.path.basename(image_path),
                'success': False,
                'error': str(e)
            }
    
    def process_folder(self, folder_path: str, parallel: bool = True) -> List[Dict]:
        """Process all images in a folder"""
        print(f"\n{'='*60}")
        print(f"BATCH PASSPORT PROCESSING")
        print(f"{'='*60}")
        print(f"Folder: {folder_path}")
        print(f"Mode: {'Parallel' if parallel else 'Sequential'}")
        
        # Find all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        image_files = []
        
        for file in os.listdir(folder_path):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_files.append(os.path.join(folder_path, file))
        
        if not image_files:
            print("No image files found!")
            return []
        
        print(f"Found {len(image_files)} images\n")
        
        # Process images
        start_time = datetime.now()
        
        if parallel:
            # Process in parallel (faster for many images)
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self.process_single_passport, path): path
                    for path in image_files
                }
                
                for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    result = future.result()
                    self.results.append(result)
                    
                    # Progress update
                    status = "✅" if result['success'] else "❌"
                    print(f"[{i}/{len(image_files)}] {status} {result['file']}")
                    if result['success']:
                        print(f"     Accuracy: {result['accuracy']}")
                    else:
                        print(f"     Error: {result['error']}")
        else:
            # Process sequentially
            for i, image_path in enumerate(image_files, 1):
                print(f"[{i}/{len(image_files)}] Processing: {os.path.basename(image_path)}")
                result = self.process_single_passport(image_path)
                self.results.append(result)
                
                if result['success']:
                    print(f"     ✅ Success - Accuracy: {result['accuracy']}")
                else:
                    print(f"     ❌ Failed - {result['error']}")
        
        # Calculate statistics
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        successful = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - successful
        
        # Print summary
        print(f"\n{'='*60}")
        print("PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Total images: {len(self.results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success rate: {(successful/len(self.results)*100):.1f}%")
        print(f"Total time: {processing_time:.2f} seconds")
        print(f"Average time: {(processing_time/len(self.results)):.2f} seconds/image")
        
        if successful > 0:
            # Calculate average accuracy
            accuracies = []
            for r in self.results:
                if r['success'] and r['accuracy']:
                    acc_str = r['accuracy'].replace('%', '')
                    try:
                        accuracies.append(float(acc_str))
                    except:
                        pass
            
            if accuracies:
                avg_accuracy = sum(accuracies) / len(accuracies)
                print(f"Average accuracy: {avg_accuracy:.1f}%")
        
        return self.results
    
    def save_results(self, output_file: str = "batch_results.json"):
        """Save batch processing results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"batch_results_{timestamp}.json"
        
        # Prepare summary data
        summary = {
            'timestamp': timestamp,
            'total_processed': len(self.results),
            'successful': sum(1 for r in self.results if r['success']),
            'failed': sum(1 for r in self.results if not r['success']),
            'results': self.results
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        # Also create CSV for easy viewing
        csv_file = f"batch_results_{timestamp}.csv"
        with open(csv_file, 'w') as f:
            # Header
            f.write("File,Success,Accuracy,Passport Number,Full Name,Nationality,DOB,Expiry,Error\n")
            
            # Data rows
            for result in self.results:
                file_name = result['file']
                success = result['success']
                accuracy = result.get('accuracy', '')
                error = result.get('error', '')
                
                if success:
                    data = result.get('data', {})
                    passport_num = data.get('passport_number', '')
                    full_name = data.get('full_name', '')
                    nationality = data.get('nationality', '')
                    dob = data.get('date_of_birth', '')
                    expiry = data.get('date_of_expiry', '')
                else:
                    passport_num = full_name = nationality = dob = expiry = ''
                
                f.write(f'"{file_name}",{success},"{accuracy}","{passport_num}","{full_name}","{nationality}","{dob}","{expiry}","{error}"\n')
        
        print(f"📊 CSV summary saved to: {csv_file}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python example_batch.py <folder_path> [--sequential]")
        print("Example: python example_batch.py passport_images/")
        print("         python example_batch.py passport_images/ --sequential")
        return
    
    folder_path = sys.argv[1]
    parallel = '--sequential' not in sys.argv
    
    # Check if folder exists
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found: {folder_path}")
        return
    
    # Check server
    try:
        response = requests.get("http://localhost:5000/health", timeout=2)
        if response.status_code != 200:
            raise Exception("Server not healthy")
    except:
        print("❌ Error: Server is not running")
        print("Start the server first: run_server.bat (Windows) or ./run_server.sh (Linux/Mac)")
        return
    
    # Process batch
    processor = BatchProcessor()
    processor.process_folder(folder_path, parallel=parallel)
    processor.save_results()

if __name__ == "__main__":
    main()