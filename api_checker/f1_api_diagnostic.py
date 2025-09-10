"""
F1 API Diagnostic Checker - Complete Endpoint Testing
Tests all F1 APIs and saves sample data to JSON for pipeline optimization
"""

import asyncio
import aiohttp
import json
import ssl
import certifi
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class F1APIDiagnostic:
    def __init__(self):
        self.output_dir = Path('api_diagnostic_results')
        self.output_dir.mkdir(exist_ok=True)
        
        # All API endpoints to test
        self.api_endpoints = {
            'jolpica_f1': {
                'base_url': 'https://api.jolpi.ca/ergast/f1',
                'name': 'Jolpica-F1 API',
                'priority': 1
            },
            'ergast_primary': {
                'base_url': 'http://ergast.com/api/f1',
                'name': 'Ergast API (HTTP)',
                'priority': 2
            },
            'ergast_https': {
                'base_url': 'https://ergast.com/api/f1',
                'name': 'Ergast API (HTTPS)',
                'priority': 2
            },
            'openf1': {
                'base_url': 'https://api.openf1.org/v1',
                'name': 'OpenF1 API',
                'priority': 1
            }
        }
        
        # Test scenarios for each API
        self.test_scenarios = {
            'race_results_recent': '2023/results.json?limit=50',
            'race_results_historical': '1990/results.json?limit=50',
            'driver_standings_recent': '2023/driverStandings.json',
            'driver_standings_historical': '1990/driverStandings.json',
            'constructor_standings_recent': '2023/constructorStandings.json',
            'constructor_standings_historical': '1990/constructorStandings.json',
            'qualifying_recent': '2023/qualifying.json?limit=50',
            'qualifying_historical': '1990/qualifying.json?limit=50',
            'circuits': 'circuits.json?limit=100',
            'drivers': 'drivers.json?limit=100',
            'constructors': 'constructors.json?limit=100',
            'seasons': 'seasons.json?limit=20',
            'pit_stops_2023': '2023/1/pitstops.json',
            'pit_stops_2022': '2022/1/pitstops.json'
        }
        
        # OpenF1 specific endpoints
        self.openf1_scenarios = {
            'sessions': 'sessions?session_key=9161',  # 2023 Bahrain GP
            'drivers_openf1': 'drivers?session_key=9161',
            'laps': 'laps?session_key=9161&driver_number=1',
            'positions': 'position?session_key=9161&driver_number=1',
            'weather': 'weather?session_key=9161'
        }
        
        self.diagnostic_results = {}
        
    async def run_complete_diagnostic(self):
        """Run comprehensive API diagnostic across all endpoints"""
        
        print("🔍 F1 API Comprehensive Diagnostic Starting")
        print("="*60)
        
        start_time = datetime.now()
        
        # Test all Ergast-compatible APIs
        await self.test_ergast_apis()
        
        # Test OpenF1 API
        await self.test_openf1_api()
        
        # Test FastF1 availability
        await self.test_fastf1_availability()
        
        # Generate comprehensive report
        self.generate_diagnostic_report()
        
        runtime = datetime.now() - start_time
        print(f"\n✅ Diagnostic completed in {runtime}")
        print(f"📄 Results saved in: {self.output_dir}/")
        
        return self.diagnostic_results
    
    async def test_ergast_apis(self):
        """Test all Ergast-compatible API endpoints"""
        
        print("\n📊 Testing Ergast-Compatible APIs...")
        
        # Create SSL context
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            
            for api_key, api_info in self.api_endpoints.items():
                if api_key == 'openf1':  # Skip OpenF1 here
                    continue
                    
                print(f"\n🔗 Testing {api_info['name']}...")
                api_results = {}
                
                for scenario_name, endpoint in self.test_scenarios.items():
                    try:
                        url = f"{api_info['base_url']}/{endpoint}"
                        print(f"   Testing: {scenario_name}")
                        
                        async with session.get(url) as response:
                            status = response.status
                            
                            if status == 200:
                                try:
                                    data = await response.json()
                                    sample_data = self.extract_sample_data(data, scenario_name)
                                    
                                    api_results[scenario_name] = {
                                        'status': 'SUCCESS',
                                        'status_code': status,
                                        'url': url,
                                        'data_available': True,
                                        'sample_count': len(sample_data.get('samples', [])),
                                        'data_structure': self.analyze_data_structure(data),
                                        'sample_data': sample_data
                                    }
                                    print(f"      ✅ Success - {len(sample_data.get('samples', []))} samples")
                                    
                                except json.JSONDecodeError:
                                    api_results[scenario_name] = {
                                        'status': 'JSON_ERROR',
                                        'status_code': status,
                                        'url': url,
                                        'error': 'Invalid JSON response'
                                    }
                                    print(f"      ❌ JSON decode error")
                                    
                            else:
                                api_results[scenario_name] = {
                                    'status': 'HTTP_ERROR',
                                    'status_code': status,
                                    'url': url,
                                    'error': f'HTTP {status}'
                                }
                                print(f"      ❌ HTTP {status}")
                                
                    except Exception as e:
                        api_results[scenario_name] = {
                            'status': 'EXCEPTION',
                            'url': f"{api_info['base_url']}/{endpoint}",
                            'error': str(e)
                        }
                        print(f"      ❌ Exception: {str(e)[:50]}...")
                    
                    await asyncio.sleep(0.2)  # Rate limiting
                
                self.diagnostic_results[api_key] = {
                    'api_info': api_info,
                    'test_results': api_results,
                    'overall_success_rate': self.calculate_success_rate(api_results)
                }
                
                # Save individual API results
                with open(self.output_dir / f'{api_key}_diagnostic.json', 'w') as f:
                    json.dump(self.diagnostic_results[api_key], f, indent=2, default=str)
    
    async def test_openf1_api(self):
        """Test OpenF1 API endpoints"""
        
        print("\n📡 Testing OpenF1 API...")
        
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=5)
        timeout = aiohttp.ClientTimeout(total=45)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            
            api_info = self.api_endpoints['openf1']
            api_results = {}
            
            for scenario_name, endpoint in self.openf1_scenarios.items():
                try:
                    url = f"{api_info['base_url']}/{endpoint}"
                    print(f"   Testing: {scenario_name}")
                    
                    async with session.get(url) as response:
                        status = response.status
                        
                        if status == 200:
                            try:
                                data = await response.json()
                                
                                if isinstance(data, list) and data:
                                    sample_data = {
                                        'total_records': len(data),
                                        'samples': data[:3],  # First 3 records
                                        'fields_available': list(data[0].keys()) if data else []
                                    }
                                    
                                    api_results[scenario_name] = {
                                        'status': 'SUCCESS',
                                        'status_code': status,
                                        'url': url,
                                        'data_available': True,
                                        'sample_count': len(data),
                                        'sample_data': sample_data
                                    }
                                    print(f"      ✅ Success - {len(data)} records")
                                    
                                else:
                                    api_results[scenario_name] = {
                                        'status': 'NO_DATA',
                                        'status_code': status,
                                        'url': url,
                                        'data': data
                                    }
                                    print(f"      ⚠️  No data returned")
                                    
                            except json.JSONDecodeError:
                                api_results[scenario_name] = {
                                    'status': 'JSON_ERROR',
                                    'status_code': status,
                                    'url': url,
                                    'error': 'Invalid JSON response'
                                }
                                print(f"      ❌ JSON decode error")
                                
                        else:
                            api_results[scenario_name] = {
                                'status': 'HTTP_ERROR',
                                'status_code': status,
                                'url': url,
                                'error': f'HTTP {status}'
                            }
                            print(f"      ❌ HTTP {status}")
                            
                except Exception as e:
                    api_results[scenario_name] = {
                        'status': 'EXCEPTION',
                        'url': f"{api_info['base_url']}/{endpoint}",
                        'error': str(e)
                    }
                    print(f"      ❌ Exception: {str(e)[:50]}...")
                
                await asyncio.sleep(0.5)  # Longer delay for OpenF1
            
            self.diagnostic_results['openf1'] = {
                'api_info': api_info,
                'test_results': api_results,
                'overall_success_rate': self.calculate_success_rate(api_results)
            }
            
            # Save OpenF1 results
            with open(self.output_dir / 'openf1_diagnostic.json', 'w') as f:
                json.dump(self.diagnostic_results['openf1'], f, indent=2, default=str)
    
    async def test_fastf1_availability(self):
        """Test FastF1 library availability and basic functionality"""
        
        print("\n🏎️ Testing FastF1 Library...")
        
        fastf1_results = {
            'library_available': False,
            'sample_data_accessible': False,
            'error': None,
            'sample_data': None
        }
        
        try:
            import fastf1
            fastf1_results['library_available'] = True
            print("   ✅ FastF1 library imported successfully")
            
            # Try to get a simple schedule
            try:
                schedule = fastf1.get_event_schedule(2023)
                if not schedule.empty:
                    fastf1_results['sample_data_accessible'] = True
                    fastf1_results['sample_data'] = {
                        'schedule_events': len(schedule),
                        'sample_events': schedule[['EventName', 'EventDate', 'Country']].head(3).to_dict('records')
                    }
                    print(f"   ✅ Schedule accessible - {len(schedule)} events for 2023")
                else:
                    print("   ⚠️  Schedule returned but empty")
                    
            except Exception as e:
                fastf1_results['error'] = f"Schedule access failed: {str(e)}"
                print(f"   ❌ Schedule access failed: {str(e)[:50]}...")
                
        except ImportError as e:
            fastf1_results['error'] = f"FastF1 not available: {str(e)}"
            print(f"   ❌ FastF1 not available: {str(e)}")
        
        self.diagnostic_results['fastf1'] = fastf1_results
        
        # Save FastF1 results
        with open(self.output_dir / 'fastf1_diagnostic.json', 'w') as f:
            json.dump(fastf1_results, f, indent=2, default=str)
    
    def extract_sample_data(self, data, scenario_name):
        """Extract meaningful sample data from API responses"""
        
        sample_data = {
            'data_type': scenario_name,
            'samples': [],
            'fields_available': [],
            'total_records': 0
        }
        
        try:
            if 'MRData' in data:
                # Ergast API format
                mrdata = data['MRData']
                
                if 'RaceTable' in mrdata and 'Races' in mrdata['RaceTable']:
                    races = mrdata['RaceTable']['Races']
                    sample_data['total_records'] = len(races)
                    
                    if 'results' in scenario_name:
                        # Race results
                        for race in races[:2]:  # First 2 races
                            for result in race.get('Results', [])[:3]:  # First 3 results per race
                                sample_data['samples'].append({
                                    'race': race.get('raceName'),
                                    'driver': result.get('Driver', {}).get('familyName'),
                                    'constructor': result.get('Constructor', {}).get('name'),
                                    'position': result.get('position'),
                                    'points': result.get('points'),
                                    'status': result.get('status')
                                })
                                if not sample_data['fields_available']:
                                    sample_data['fields_available'] = list(result.keys())
                    
                    elif 'qualifying' in scenario_name:
                        # Qualifying results
                        for race in races[:2]:
                            for result in race.get('QualifyingResults', [])[:3]:
                                sample_data['samples'].append({
                                    'race': race.get('raceName'),
                                    'driver': result.get('Driver', {}).get('familyName'),
                                    'position': result.get('position'),
                                    'q1': result.get('Q1'),
                                    'q2': result.get('Q2'),
                                    'q3': result.get('Q3')
                                })
                                if not sample_data['fields_available']:
                                    sample_data['fields_available'] = list(result.keys())
                    
                    elif 'pitstops' in scenario_name:
                        # Pit stop data
                        for race in races:
                            for pitstop in race.get('PitStops', [])[:5]:
                                sample_data['samples'].append({
                                    'driver': pitstop.get('driverId'),
                                    'stop': pitstop.get('stop'),
                                    'lap': pitstop.get('lap'),
                                    'time': pitstop.get('time'),
                                    'duration': pitstop.get('duration')
                                })
                                if not sample_data['fields_available']:
                                    sample_data['fields_available'] = list(pitstop.keys())
                
                elif 'StandingsTable' in mrdata:
                    # Championship standings
                    standings_lists = mrdata['StandingsTable'].get('StandingsLists', [])
                    
                    if standings_lists:
                        if 'DriverStandings' in standings_lists[0]:
                            standings = standings_lists[0]['DriverStandings']
                            sample_data['total_records'] = len(standings)
                            
                            for standing in standings[:5]:  # Top 5
                                sample_data['samples'].append({
                                    'driver': standing.get('Driver', {}).get('familyName'),
                                    'constructor': standing.get('Constructors', [{}])[0].get('name'),
                                    'position': standing.get('position'),
                                    'points': standing.get('points'),
                                    'wins': standing.get('wins')
                                })
                                if not sample_data['fields_available']:
                                    sample_data['fields_available'] = list(standing.keys())
                        
                        elif 'ConstructorStandings' in standings_lists[0]:
                            standings = standings_lists[0]['ConstructorStandings']
                            sample_data['total_records'] = len(standings)
                            
                            for standing in standings[:5]:  # Top 5
                                sample_data['samples'].append({
                                    'constructor': standing.get('Constructor', {}).get('name'),
                                    'position': standing.get('position'),
                                    'points': standing.get('points'),
                                    'wins': standing.get('wins')
                                })
                                if not sample_data['fields_available']:
                                    sample_data['fields_available'] = list(standing.keys())
                
                elif 'CircuitTable' in mrdata:
                    # Circuits
                    circuits = mrdata['CircuitTable'].get('Circuits', [])
                    sample_data['total_records'] = len(circuits)
                    
                    for circuit in circuits[:5]:
                        sample_data['samples'].append({
                            'circuitId': circuit.get('circuitId'),
                            'circuitName': circuit.get('circuitName'),
                            'location': circuit.get('Location', {}).get('locality'),
                            'country': circuit.get('Location', {}).get('country'),
                            'lat': circuit.get('Location', {}).get('lat'),
                            'long': circuit.get('Location', {}).get('long')
                        })
                        if not sample_data['fields_available']:
                            sample_data['fields_available'] = list(circuit.keys())
                
                elif 'DriverTable' in mrdata:
                    # Drivers
                    drivers = mrdata['DriverTable'].get('Drivers', [])
                    sample_data['total_records'] = len(drivers)
                    
                    for driver in drivers[:5]:
                        sample_data['samples'].append({
                            'driverId': driver.get('driverId'),
                            'givenName': driver.get('givenName'),
                            'familyName': driver.get('familyName'),
                            'nationality': driver.get('nationality'),
                            'dateOfBirth': driver.get('dateOfBirth')
                        })
                        if not sample_data['fields_available']:
                            sample_data['fields_available'] = list(driver.keys())
                
                elif 'ConstructorTable' in mrdata:
                    # Constructors
                    constructors = mrdata['ConstructorTable'].get('Constructors', [])
                    sample_data['total_records'] = len(constructors)
                    
                    for constructor in constructors[:5]:
                        sample_data['samples'].append({
                            'constructorId': constructor.get('constructorId'),
                            'name': constructor.get('name'),
                            'nationality': constructor.get('nationality'),
                            'url': constructor.get('url')
                        })
                        if not sample_data['fields_available']:
                            sample_data['fields_available'] = list(constructor.keys())
                
                elif 'SeasonTable' in mrdata:
                    # Seasons
                    seasons = mrdata['SeasonTable'].get('Seasons', [])
                    sample_data['total_records'] = len(seasons)
                    
                    for season in seasons[-5:]:  # Last 5 seasons
                        sample_data['samples'].append({
                            'season': season.get('season'),
                            'url': season.get('url')
                        })
                        if not sample_data['fields_available']:
                            sample_data['fields_available'] = list(season.keys())
        
        except Exception as e:
            sample_data['extraction_error'] = str(e)
        
        return sample_data
    
    def analyze_data_structure(self, data):
        """Analyze the structure of returned data"""
        
        structure = {
            'root_keys': list(data.keys()) if isinstance(data, dict) else ['non_dict_response'],
            'data_format': 'ergast_standard' if 'MRData' in data else 'other',
            'has_pagination': False,
            'estimated_total_records': 0
        }
        
        try:
            if 'MRData' in data:
                mrdata = data['MRData']
                structure['has_pagination'] = 'limit' in mrdata or 'offset' in mrdata
                structure['total_records'] = mrdata.get('total', 0)
                
                # Identify data type
                if 'RaceTable' in mrdata:
                    structure['data_type'] = 'race_data'
                    races = mrdata['RaceTable'].get('Races', [])
                    if races and 'Results' in races[0]:
                        structure['estimated_total_records'] = sum(len(race.get('Results', [])) for race in races)
                elif 'StandingsTable' in mrdata:
                    structure['data_type'] = 'standings_data'
                elif 'CircuitTable' in mrdata:
                    structure['data_type'] = 'circuit_data'
                elif 'DriverTable' in mrdata:
                    structure['data_type'] = 'driver_data'
                elif 'ConstructorTable' in mrdata:
                    structure['data_type'] = 'constructor_data'
                
        except Exception as e:
            structure['analysis_error'] = str(e)
        
        return structure
    
    def calculate_success_rate(self, api_results):
        """Calculate success rate for an API"""
        
        if not api_results:
            return 0.0
        
        successful = sum(1 for result in api_results.values() if result.get('status') == 'SUCCESS')
        total = len(api_results)
        
        return round((successful / total) * 100, 1)
    
    def generate_diagnostic_report(self):
        """Generate comprehensive diagnostic report"""
        
        print("\n" + "="*60)
        print("📋 F1 API DIAGNOSTIC REPORT")
        print("="*60)
        
        report = {
            'diagnostic_timestamp': datetime.now().isoformat(),
            'apis_tested': len(self.diagnostic_results),
            'overall_summary': {},
            'recommendations': [],
            'detailed_results': self.diagnostic_results
        }
        
        print(f"\n🔍 APIs Tested: {len(self.diagnostic_results)}")
        
        for api_name, results in self.diagnostic_results.items():
            if api_name == 'fastf1':
                status = "✅ Available" if results.get('library_available') else "❌ Not Available"
                print(f"   {api_name.upper():15} {status}")
                
                if results.get('library_available'):
                    data_status = "✅ Accessible" if results.get('sample_data_accessible') else "❌ Issues"
                    print(f"   {'Data Access':15} {data_status}")
                
            else:
                success_rate = results.get('overall_success_rate', 0)
                status = "✅ Excellent" if success_rate >= 80 else "⚠️  Partial" if success_rate >= 50 else "❌ Poor"
                print(f"   {results['api_info']['name']:25} {status} ({success_rate}%)")
        
        # Generate recommendations
        recommendations = self.generate_recommendations()
        report['recommendations'] = recommendations
        
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        # Save comprehensive report
        with open(self.output_dir / 'comprehensive_diagnostic_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Complete diagnostic report saved to:")
        print(f"    {self.output_dir}/comprehensive_diagnostic_report.json")
        
        return report
    
    def generate_recommendations(self):
        """Generate recommendations based on diagnostic results"""
        
        recommendations = []
        
        # Analyze API performance
        working_apis = []
        failed_apis = []
        
        for api_name, results in self.diagnostic_results.items():
            if api_name == 'fastf1':
                if results.get('library_available') and results.get('sample_data_accessible'):
                    working_apis.append('FastF1')
                elif not results.get('library_available'):
                    recommendations.append("Install FastF1 library: pip install fastf1")
            else:
                success_rate = results.get('overall_success_rate', 0)
                if success_rate >= 70:
                    working_apis.append(results['api_info']['name'])
                else:
                    failed_apis.append(results['api_info']['name'])
        
        if working_apis:
            recommendations.append(f"Use these reliable APIs: {', '.join(working_apis)}")
        
        if failed_apis:
            recommendations.append(f"Avoid or add fallbacks for: {', '.join(failed_apis)}")
        
        # Data-specific recommendations
        has_recent_data = False
        has_historical_data = False
        
        for api_name, results in self.diagnostic_results.items():
            if api_name == 'fastf1':
                continue
                
            test_results = results.get('test_results', {})
            
            for scenario, result in test_results.items():
                if result.get('status') == 'SUCCESS':
                    if 'recent' in scenario or '2023' in scenario:
                        has_recent_data = True
                    if 'historical' in scenario or '1990' in scenario:
                        has_historical_data = True
        
        if has_recent_data and not has_historical_data:
            recommendations.append("Historical data (pre-2000) may be limited - focus on modern era (2000+)")
        elif has_historical_data and not has_recent_data:
            recommendations.append("Recent data may have issues - verify current season availability")
        elif has_recent_data and has_historical_data:
            recommendations.append("Full historical span (1950-2025) appears achievable")
        
        if not recommendations:
            recommendations.append("All APIs appear to have significant issues - consider alternative approaches")
        
        return recommendations

async def main():
    """Run the complete F1 API diagnostic"""
    
    diagnostic = F1APIDiagnostic()
    results = await diagnostic.run_complete_diagnostic()
    
    print(f"\n🎯 Next Steps:")
    print(f"1. Review the JSON files in '{diagnostic.output_dir}/'")
    print(f"2. Share the comprehensive_diagnostic_report.json with your developer")
    print(f"3. Use the findings to build an optimized, error-free data collector")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
