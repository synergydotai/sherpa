"""
Sherpa

A Streamlit application for analyzing and visualizing Bittensor subnets using the
Subnet Classification Framework.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import os
import shutil
from datetime import datetime
import sqlite3
import uuid
from PIL import Image
import io

# Database setup and helper functions
DB_PATH = "subnets.db"

def init_db():
    """Initialize the database with the necessary tables."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create subnets table if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS subnets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT,
        name TEXT NOT NULL,
        description TEXT,
        service_oriented_scores TEXT,
        research_oriented_scores TEXT,
        intelligence_oriented_scores TEXT,
        resource_oriented_scores TEXT,
        additional_criteria_scores TEXT,
        service_research_score REAL,
        intelligence_resource_score REAL,
        total_score REAL,
        tier TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    
    # Create directories for frameworks, compass, and backups if they don't exist
    os.makedirs('frameworks', exist_ok=True)
    os.makedirs('compass', exist_ok=True)
    os.makedirs('backup/frameworks', exist_ok=True)
    os.makedirs('backup/compass', exist_ok=True)
    
    # Initialize backups if they don't exist
    init_backups()

def init_backups():
    """Initialize backup directories and create initial backups if needed."""
    print("Initializing backup system...")
    
    # Create backup directories if they don't exist
    os.makedirs('backup/frameworks', exist_ok=True)
    os.makedirs('backup/compass', exist_ok=True)
    
    # Check if we need to create initial backups
    frameworks_dir = 'frameworks'
    compass_dir = 'compass'
    frameworks_backup_dir = 'backup/frameworks'
    compass_backup_dir = 'backup/compass'
    
    # Backup all frameworks if backup directory is empty
    if os.path.exists(frameworks_dir):
        if not os.listdir(frameworks_backup_dir):
            for filename in os.listdir(frameworks_dir):
                if filename.endswith('.json'):
                    src_file = os.path.join(frameworks_dir, filename)
                    dst_file = os.path.join(frameworks_backup_dir, filename)
                    try:
                        shutil.copy2(src_file, dst_file)
                        print(f"Created initial backup for {filename}")
                    except Exception as e:
                        print(f"Error creating backup for {filename}: {str(e)}")
    
    # Backup all compasses if backup directory is empty
    if os.path.exists(compass_dir):
        if not os.listdir(compass_backup_dir):
            for filename in os.listdir(compass_dir):
                if filename.endswith('.json'):
                    src_file = os.path.join(compass_dir, filename)
                    dst_file = os.path.join(compass_backup_dir, filename)
                    try:
                        shutil.copy2(src_file, dst_file)
                        print(f"Created initial backup for {filename}")
                    except Exception as e:
                        print(f"Error creating backup for {filename}: {str(e)}")

def backup_framework(filepath):
    """Create a backup of a framework file."""
    try:
        filename = os.path.basename(filepath)
        backup_path = os.path.join('backup/frameworks', filename)
        
        # Create backup
        shutil.copy2(filepath, backup_path)
        print(f"Created backup of {filename}")
        return True
    except Exception as e:
        print(f"Error creating backup of {filepath}: {str(e)}")
        return False

def save_framework(framework_data, filename=None):
    """Save a framework to a JSON file."""
    try:
        if not filename:
            # Generate filename from framework name
            filename = f"frameworks/{framework_data['name'].lower().replace(' ', '_')}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Set active status to True by default if it doesn't exist
        if 'active' not in framework_data:
            framework_data['active'] = True
        
        # Update timestamp
        framework_data['updated_at'] = datetime.now().isoformat()
        
        # If the file already exists, create a backup before overwriting
        if os.path.exists(filename):
            backup_framework(filename)
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(framework_data, f, indent=4)
        
        return True, filename
    except Exception as e:
        print(f"Error saving framework: {str(e)}")
        return False, str(e)

def load_frameworks(only_active=False):
    """
    Load all frameworks from the frameworks directory.
    
    Parameters:
    - only_active (bool): If True, only return frameworks with active=True
    """
    frameworks = []
    try:
        if not os.path.exists('frameworks'):
            os.makedirs('frameworks')
            return frameworks
            
        for filename in os.listdir('frameworks'):
            if filename.endswith('.json'):
                filepath = os.path.join('frameworks', filename)
                try:
                    with open(filepath, 'r') as f:
                        try:
                            framework = json.load(f)
                            
                            # Set active to True by default if not present
                            if 'active' not in framework:
                                framework['active'] = True
                            
                            # Skip inactive frameworks if only_active is True
                            if only_active and not framework.get('active', True):
                                continue
                            
                            # Normalize criteria format (handle both old and new formats)
                            if 'criteria' in framework:
                                for category, criteria in framework['criteria'].items():
                                    for key, value in list(criteria.items()):
                                        # Handle string format (old format or JSON string)
                                        if isinstance(value, str):
                                            if value.startswith('{') and 'question' in value:
                                                # This is a JSON string representation of the new format
                                                try:
                                                    import ast
                                                    parsed_value = ast.literal_eval(value)
                                                    criteria[key] = parsed_value
                                                except Exception as e:
                                                    # If parsing fails, convert to basic format
                                                    criteria[key] = {
                                                        "question": value,
                                                        "description": ""
                                                    }
                                            else:
                                                # This is a simple string (old format) - convert to new format
                                                criteria[key] = {
                                                    "question": value,
                                                    "description": ""
                                                }
                            
                            # Normalize additional criteria format
                            if 'additional_criteria' in framework:
                                for key, data in framework['additional_criteria'].items():
                                    if isinstance(data, dict):
                                        # Ensure it has both question and description
                                        if 'question' not in data and 'description' in data:
                                            data['question'] = data['description']
                                        elif 'description' not in data and 'question' in data:
                                            data['description'] = ""
                                            
                            framework['_filepath'] = filepath  # Store filepath for reference
                            frameworks.append(framework)
                        except json.JSONDecodeError as json_err:
                            print(f"Error parsing JSON in {filepath}: {str(json_err)}")
                except (IOError, PermissionError) as file_err:
                    print(f"Error opening file {filepath}: {str(file_err)}")
        return frameworks
    except Exception as e:
        print(f"Error loading frameworks: {str(e)}")
        return frameworks

def delete_framework(filepath):
    """Delete a framework file, but first ensure a backup exists."""
    try:
        # Create a backup before deleting
        backup_framework(filepath)
        
        # Now delete the file
        os.remove(filepath)
        return True
    except Exception as e:
        print(f"Error deleting framework: {str(e)}")
        return False

def backup_compass(filepath):
    """Create a backup of a compass file."""
    try:
        filename = os.path.basename(filepath)
        backup_path = os.path.join('backup/compass', filename)
        
        # Create backup
        shutil.copy2(filepath, backup_path)
        print(f"Created backup of {filename}")
        return True
    except Exception as e:
        print(f"Error creating backup of {filepath}: {str(e)}")
        return False

def save_compass(compass_data, filename=None):
    """Save a compass (assessment) to a JSON file."""
    try:
        if not filename:
            # Generate filename from compass name and framework
            base_name = f"{compass_data['name'].lower().replace(' ', '_')}"
            counter = 1
            filename = f"compass/{base_name}.json"
            
            # Avoid overwriting existing files by adding counter
            while os.path.exists(filename):
                filename = f"compass/{base_name}_{counter}.json"
                counter += 1
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # If the file already exists, create a backup before overwriting
        if os.path.exists(filename):
            backup_compass(filename)
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(compass_data, f, indent=4)
        
        return True, filename
    except Exception as e:
        print(f"Error saving compass: {str(e)}")
        return False, str(e)

def load_compasses():
    """Load all compasses from the compass directory."""
    compasses = []
    try:
        if not os.path.exists('compass'):
            os.makedirs('compass')
            return compasses
            
        for filename in os.listdir('compass'):
            if filename.endswith('.json'):
                filepath = os.path.join('compass', filename)
                try:
                    with open(filepath, 'r') as f:
                        try:
                            compass = json.load(f)
                            compass['_filepath'] = filepath  # Store filepath for reference
                            compass['enabled'] = True  # Add enabled flag (default to True)
                            compasses.append(compass)
                        except json.JSONDecodeError as json_err:
                            print(f"Error parsing JSON in {filepath}: {str(json_err)}")
                except (IOError, PermissionError) as file_err:
                    print(f"Error opening file {filepath}: {str(file_err)}")
        return compasses
    except Exception as e:
        print(f"Error loading compasses: {str(e)}")
        return compasses

def delete_compass(filepath):
    """Delete a compass file, but first ensure a backup exists."""
    try:
        # Create a backup before deleting
        backup_compass(filepath)
        
        # Now delete the file
        os.remove(filepath)
        return True
    except Exception as e:
        print(f"Error deleting compass: {str(e)}")
        return False

def get_subnets():
    """Get all subnets from the database."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM subnets", conn)
    conn.close()
    
    if not df.empty:
        # Convert JSON strings to dictionaries
        for col in ['service_oriented_scores', 'research_oriented_scores', 
                   'intelligence_oriented_scores', 'resource_oriented_scores',
                   'additional_criteria_scores', 'service_research_score', 'intelligence_resource_score']:
            df[col] = df[col].apply(lambda x: json.loads(x) if x else {})
        
        # Calcular los valores promedio para cada subnet (necesarios para los gráficos)
        df['service_avg'] = df['service_oriented_scores'].apply(
            lambda x: sum(x.values()) / len(x) if x and len(x) > 0 else 0
        )
        df['research_avg'] = df['research_oriented_scores'].apply(
            lambda x: sum(x.values()) / len(x) if x and len(x) > 0 else 0
        )
        df['intelligence_avg'] = df['intelligence_oriented_scores'].apply(
            lambda x: sum(x.values()) / len(x) if x and len(x) > 0 else 0
        )
        df['resource_avg'] = df['resource_oriented_scores'].apply(
            lambda x: sum(x.values()) / len(x) if x and len(x) > 0 else 0
        )
            
    return df

def save_subnet(subnet_data):
    """Save a subnet to the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Prepare data for insertion
    service_scores = json.dumps(subnet_data.get('service_oriented_scores', {}))
    research_scores = json.dumps(subnet_data.get('research_oriented_scores', {}))
    intelligence_scores = json.dumps(subnet_data.get('intelligence_oriented_scores', {}))
    resource_scores = json.dumps(subnet_data.get('resource_oriented_scores', {}))
    additional_scores = json.dumps(subnet_data.get('additional_criteria_scores', {}))
    
    # Calculate scores
    scores = calculate_scores(
        subnet_data.get('service_oriented_scores', {}),
        subnet_data.get('research_oriented_scores', {}),
        subnet_data.get('intelligence_oriented_scores', {}),
        subnet_data.get('resource_oriented_scores', {}),
        subnet_data.get('additional_criteria_scores', {}).get('scores', {}),
        subnet_data.get('additional_criteria_scores', {}).get('weights', {})
    )
    
    # Extract calculated scores and convert tuples to JSON strings where needed
    service_research_score = json.dumps(scores.get('service_research_score'))
    intelligence_resource_score = json.dumps(scores.get('intelligence_resource_score'))
    total_score = scores.get('total_score')
    tier = scores.get('tier')
    
    # Insert or update subnet
    if 'id' in subnet_data and subnet_data['id']:
        # Update existing subnet
        c.execute('''
        UPDATE subnets 
        SET name=?, uid=?, description=?, 
            service_oriented_scores=?, research_oriented_scores=?,
            intelligence_oriented_scores=?, resource_oriented_scores=?,
            additional_criteria_scores=?,
            service_research_score=?, intelligence_resource_score=?,
            total_score=?, tier=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        ''', (
            subnet_data.get('name', ''),
            subnet_data.get('uid', ''),
            subnet_data.get('description', ''),
            service_scores, research_scores,
            intelligence_scores, resource_scores,
            additional_scores,
            service_research_score, intelligence_resource_score,
            total_score, tier,
            subnet_data['id']
        ))
    else:
        # Insert new subnet
        c.execute('''
        INSERT INTO subnets 
        (name, uid, description, 
         service_oriented_scores, research_oriented_scores,
         intelligence_oriented_scores, resource_oriented_scores,
         additional_criteria_scores,
         service_research_score, intelligence_resource_score,
         total_score, tier)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            subnet_data.get('name', ''),
            subnet_data.get('uid', ''),
            subnet_data.get('description', ''),
            service_scores, research_scores,
            intelligence_scores, resource_scores,
            additional_scores,
            service_research_score, intelligence_resource_score,
            total_score, tier
        ))
    
    conn.commit()
    conn.close()

def delete_subnet(subnet_id):
    """Delete a subnet from the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("DELETE FROM subnets WHERE id=?", (subnet_id,))
    
    conn.commit()
    conn.close()

def clear_all_subnets():
    """Clear all subnets from the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("DELETE FROM subnets")
    
    conn.commit()
    conn.close()

# Evaluation criteria and scoring functions
def get_evaluation_criteria():
    """Return the evaluation criteria for the subnet framework."""
    criteria = {
        "service": {
            "functioning_product": {
                "question": "Does it have a functioning product or service?",
                "description": "Evaluate whether the subnet has an actual working product or service that can be used by validators and/or end-users."
            },
            "immediate_utility": {
                "question": "Does it offer immediate, tangible utility?",
                "description": "Assess if the subnet provides value that can be utilized right now, rather than just future potential."
            },
            "revenue_model": {
                "question": "Is there a clear, current revenue model?",
                "description": "Determine if there is a defined way for the subnet to generate revenue, both for the project and potentially for validators."
            },
            "apis_integrations": {
                "question": "Are there ready-to-use APIs or integrations?",
                "description": "Check if the subnet offers well-documented APIs or integrations that developers can easily implement."
            },
            "validator_monetization": {
                "question": "Can validators monetize their bandwidth?",
                "description": "Evaluate whether validators running the subnet can earn rewards or monetize their contribution."
            },
            "usage_metrics": {
                "question": "Are there measurable usage or adoption metrics?",
                "description": "Determine if the subnet tracks and shares metrics about its usage, adoption, or performance."
            },
            "implementation_docs": {
                "question": "Is there documentation geared toward implementation?",
                "description": "Check if comprehensive documentation exists to help with practical implementation and integration."
            },
            "real_world_use_cases": {
                "question": "Are there real-world use cases implemented?",
                "description": "Evaluate whether the subnet has demonstrated actual use cases in real-world scenarios."
            }
        },
        "research": {
            "fundamental_problems": {
                "question": "Are they solving fundamental problems?",
                "description": "Assess if the subnet addresses core technical or scientific challenges in its field."
            },
            "academic_publications": {
                "question": "Do they have academic or technical publications?",
                "description": "Check if the team has published research papers, technical documents, or whitepapers about their work."
            },
            "research_background": {
                "question": "Does the team have an academic/research background?",
                "description": "Evaluate whether the team members have credentials or experience in academic or research settings."
            },
            "technical_roadmap": {
                "question": "Does the roadmap prioritize technical innovation?",
                "description": "Determine if the development roadmap focuses on advancing technical capabilities over commercial features."
            },
            "academic_collaboration": {
                "question": "Do they collaborate with academic institutions?",
                "description": "Check if the subnet project works with universities or research institutions."
            },
            "emerging_tech": {
                "question": "Are they working on emerging technologies?",
                "description": "Assess if the subnet uses or develops cutting-edge technologies rather than established solutions."
            },
            "scientific_goals": {
                "question": "Are their goals more scientific than commercial?",
                "description": "Evaluate if the subnet's primary aims are advancing knowledge or science rather than profit."
            }
        },
        "intelligence": {
            "intelligent_processing": {
                "question": "Does it perform intelligent data processing?",
                "description": "Determine if the subnet uses AI, machine learning, or other intelligent systems to process data."
            },
            "specialized_expertise": {
                "question": "Does it require specialized expertise to build?",
                "description": "Assess whether creating or contributing to the subnet requires advanced technical knowledge or skills."
            },
            "new_insights": {
                "question": "Does it generate new insights or intelligence?",
                "description": "Evaluate if the subnet creates new knowledge, predictions, or analysis rather than just processing existing information."
            },
            "intellectual_barrier": {
                "question": "Is there a high intellectual barrier to entry?",
                "description": "Check if the subnet's field has significant intellectual challenges that limit competition."
            },
            "learning_improvement": {
                "question": "Does it learn and improve over time?",
                "description": "Determine if the subnet incorporates mechanisms to learn from data and improve its performance automatically."
            }
        },
        "resource": {
            "computational_value": {
                "question": "Does it provide computational value?",
                "description": "Assess if the subnet offers valuable computational resources or processing power to the network."
            },
            "hardware_requirements": {
                "question": "Does it have specific hardware requirements?",
                "description": "Check if running the subnet requires specialized hardware such as GPUs, large storage, or other specific resources."
            },
            "resource_provider": {
                "question": "Is its primary role being a resource provider?",
                "description": "Determine if the subnet's main function is to provide resources rather than services or intelligence."
            },
            "geographic_importance": {
                "question": "Is geographic distribution important?",
                "description": "Evaluate whether the subnet benefits from having validators distributed across different geographic locations."
            },
            "redundancy_value": {
                "question": "Does it benefit from redundancy?",
                "description": "Assess if having multiple validators performing the same function improves the subnet's reliability or performance."
            },
            "resource_returns": {
                "question": "Does it optimize for resource efficiency returns?",
                "description": "Check if the subnet is designed to maximize the return on resources invested by validators."
            }
        }
    }
    
    return criteria

def get_additional_evaluation_criteria():
    """Return the additional evaluation criteria with default weights."""
    return {
        "substrate_registration": {
            "weight": 0.9,
            "type": "positive",
            "question": "Is the subnet registered on Polkadot substrate?",
            "description": "Verify if the subnet has completed formal registration on the Polkadot substrate, which provides additional security and interoperability benefits."
        },
        "current_revenue": {
            "weight": 0.7,
            "type": "positive",
            "question": "Is the subnet currently generating revenue?",
            "description": "Assess whether the subnet is already generating real revenue streams, rather than just having potential future monetization."
        },
        "revenue_prospects": {
            "weight": 0.6,
            "type": "positive",
            "question": "Does the subnet have strong revenue prospects?",
            "description": "Evaluate the potential for future revenue growth based on the subnet's business model and market opportunity."
        },
        "team_quantifiable": {
            "weight": 0.5,
            "type": "positive",
            "question": "Is the team quantifiable and identified?",
            "description": "Determine if the team members are publicly known, with verifiable identities and roles within the project."
        },
        "team_track_record": {
            "weight": 0.5,
            "type": "positive",
            "question": "Does the team have a proven track record?",
            "description": "Evaluate the team's past experience and success in relevant fields, such as blockchain, AI, or the specific domain of the subnet."
        },
        "competitive_viability": {
            "weight": 0.7,
            "type": "positive",
            "question": "Is the subnet competitively viable in its market?",
            "description": "Assess how well the subnet can compete against both blockchain and traditional alternatives in its target market."
        },
        "total_addressable_market": {
            "weight": 0.6,
            "type": "positive",
            "question": "How large is the total addressable market?",
            "description": "Estimate the size of the potential market that the subnet could serve with its products or services."
        },
        "roadmap_quality": {
            "weight": 0.4,
            "type": "positive",
            "question": "Quality and detail of the roadmap",
            "description": "Evaluate how well-defined, realistic, and comprehensive the project's development roadmap is."
        },
        "documentation_quality": {
            "weight": 0.5,
            "type": "positive",
            "question": "Quality and completeness of documentation",
            "description": "Assess the thoroughness, clarity, and usefulness of the subnet's technical and user documentation."
        },
        "ui_ux_quality": {
            "weight": 0.4,
            "type": "positive",
            "question": "Quality of UI/UX and user experience",
            "description": "Evaluate the intuitiveness, design quality, and overall usability of the subnet's interfaces."
        },
        "github_activity": {
            "weight": 0.3,
            "type": "positive",
            "question": "Level of GitHub activity and development",
            "description": "Measure the frequency of code updates, number of contributors, and overall development activity in the project's repositories."
        },
        "twitter_activity": {
            "weight": 0.2,
            "type": "positive",
            "question": "Social media presence and activity",
            "description": "Assess the subnet's engagement with its community through social media platforms like Twitter, Discord, or Telegram."
        },
        "dtao_marketing": {
            "weight": 0.3,
            "type": "bidirectional",
            "question": "DAO/community marketing and promotion",
            "description": "Evaluate how effectively the project's DAO or community contributes to marketing and promoting the subnet."
        },
        "third_party_integrations": {
            "weight": 0.4,
            "type": "positive",
            "question": "Integration with third-party services",
            "description": "Assess the subnet's compatibility and integration with external services, platforms, or applications."
        },
        "partnerships": {
            "weight": 0.4,
            "type": "positive",
            "question": "Strategic partnerships and collaborations",
            "description": "Evaluate the quality and relevance of formal partnerships the subnet has established with other projects or organizations."
        },
        "subnet_uniqueness": {
            "weight": 0.6,
            "type": "positive",
            "question": "Uniqueness compared to other subnets",
            "description": "Determine how differentiated the subnet is from other subnets in the Bittensor ecosystem."
        },
        "interoperability": {
            "weight": 0.5,
            "type": "positive",
            "question": "Interoperability with other blockchain systems",
            "description": "Assess the subnet's ability to connect and interact with other blockchain networks and protocols."
        },
        "miner_rewards": {
            "weight": 0.4,
            "type": "positive",
            "question": "Rewards structure for miners/validators",
            "description": "Evaluate the fairness, sustainability, and incentive alignment of the subnet's reward mechanism for validators."
        },
        "subnet_integration": {
            "weight": 0.7,
            "type": "positive",
            "question": "Integration with the broader Bittensor ecosystem",
            "description": "Assess how well the subnet leverages and contributes to the wider Bittensor network and its capabilities."
        }
    }

def calculate_scores(service_scores, research_scores, intelligence_scores, resource_scores, additional_scores=None, custom_weights=None):
    """
    Calculate the subnet scores based on input criteria.
    Returns service_research_score, intelligence_resource_score, total_score, and tier.
    """
    # Calculate average for each axis
    service_avg = sum(service_scores.values()) / len(service_scores) if service_scores else 0
    research_avg = sum(research_scores.values()) / len(research_scores) if research_scores else 0
    intelligence_avg = sum(intelligence_scores.values()) / len(intelligence_scores) if intelligence_scores else 0
    resource_avg = sum(resource_scores.values()) / len(resource_scores) if resource_scores else 0
    
    # Calculate combined scores for plotting
    service_research_score = ((service_avg * 2) - 10, (research_avg * 2) - 10)  # Transform to -10 to 10 scale
    intelligence_resource_score = ((intelligence_avg * 2) - 10, (resource_avg * 2) - 10)
    
    # Calculate additional criteria score if provided
    additional_score = 0
    if additional_scores and custom_weights:
        weighted_scores = []
        for key, score in additional_scores.items():
            if key in custom_weights:
                weight_data = custom_weights[key]
                weight = weight_data.get('weight', 0.5)
                criteria_type = weight_data.get('type', 'positive')
                
                if criteria_type == 'positive':
                    weighted_scores.append(score * weight)
                elif criteria_type == 'negative':
                    weighted_scores.append((10 - score) * weight)  # Invert the scale for negative criteria
                else:  # bidirectional
                    if score >= 5:  # Above neutral is positive
                        weighted_scores.append(score * weight)
                    else:  # Below neutral is negative
                        weighted_scores.append((10 - score) * weight * -1)
        
        if weighted_scores:
            additional_score = sum(weighted_scores) / (len(weighted_scores) * 5)  # Normalize to 0-1 scale
    
    # Calculate base score (average of all criteria)
    base_score = (service_avg + research_avg + intelligence_avg + resource_avg) / 4
    
    # Apply additional criteria modifier
    total_score = base_score + additional_score
    
    # Determine tier based on total score
    if total_score >= 8.5:
        tier = "Tier A"
    elif total_score >= 7:
        tier = "Tier B"
    elif total_score >= 5.5:
        tier = "Tier C"
    else:
        tier = "Tier D"
    
    return {
        'service_research_score': service_research_score,
        'intelligence_resource_score': intelligence_resource_score,
        'total_score': total_score,
        'tier': tier,
        'base_score': base_score,
        'additional_score': additional_score,
        'service_avg': service_avg,
        'research_avg': research_avg,
        'intelligence_avg': intelligence_avg,
        'resource_avg': resource_avg
    }

# Streamlit app functions
def set_page_config():
    """Set Streamlit page configuration."""
    st.set_page_config(
        page_title="Sherpa",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Check for admin route
    query_params = st.query_params
    path = query_params.get("page", "")
    if path == "xerpa":
        admin_console_page()
        st.stop()
    
    # Apply custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
    }
    .subsection-header {
        font-size: 1.4rem;
        font-weight: 600;
        margin: 1rem 0 0.8rem 0;
        color: #4d68e9;
    }
    .tier-a {
        color: #3dc5bd;
        font-weight: bold;
    }
    .tier-b {
        color: #5884c5;
        font-weight: bold;
    }
    .tier-c {
        color: #f4be55;
        font-weight: bold;
    }
    .tier-d {
        color: #ff9f64;
        font-weight: bold;
    }
    .stSlider {
        padding-bottom: 1rem;
    }
    .stSlider label {
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    .slider-value {
        font-weight: bold;
        font-size: 1.1rem;
        margin-top: -0.5rem;
        margin-bottom: 0.5rem;
    }
    .st-emotion-cache-1kyxreq {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
    }
    .custom-info-box {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #4d68e9;
    }
    .criteria-section {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .badge {
        border-radius: 4px;
        padding: 0.2rem 0.5rem;
        font-size: 0.8rem;
        font-weight: 500;
        display: inline-block;
        margin-left: 0.5rem;
    }
    .badge-positive {
        background-color: #28a745;
        color: white;
    }
    .badge-negative {
        background-color: #dc3545;
        color: white;
    }
    .badge-bidirectional {
        background-color: #ffc107;
        color: black;
    }
    /* Tooltips for criteria descriptions */
    .coming-soon {
        font-size: 1.3em;
        color: #888;
        font-weight: 600;
    }
    
    /* Tooltip styles */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    /* Tooltip text */
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 250px;
        background-color: #555;
        color: #fff;
        text-align: left;
        border-radius: 6px;
        padding: 8px;
        position: absolute;
        z-index: 1000;
        bottom: 125%;
        left: 50%;
        margin-left: -125px;
        opacity: 0;
        transition: opacity 0.3s;
        font-weight: normal;
        font-size: 12px;
        line-height: 1.4;
    }
    
    /* Tooltip arrow */
    .tooltip .tooltiptext::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: #555 transparent transparent transparent;
    }
    
    /* Show the tooltip on hover */
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    .fine-adjust {
        font-size: 0.9rem;
        margin-top: -0.8rem;
        margin-bottom: 0.3rem;
        text-align: right;
    }
    
    /* Estilos para los botones de navegación */
    .stButton button {
        width: 100%;
        margin-bottom: 8px;
        border-radius: 5px;
    }
    
    .sidebar h3 {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #333;
    }
    
    /* Estilo para el botón de navegación activo */
    .active-nav {
        border-left: 4px solid #4d68e9;
        background-color: #f0f3ff !important;
        font-weight: bold;
    }
    
    /* Ajustar altura de los botones */
    .stButton button {
        height: auto;
        padding: 8px 16px;
    }
    
    /* Desactivar interacción en imágenes del roadmap */
    .no-interact img {
        pointer-events: none !important;
        cursor: default !important;
    }
    
    /* Eliminar el borde de expansión y el efecto hover en las imágenes */
    .no-interact img:hover {
        border: none !important;
        transform: none !important;
        box-shadow: none !important;
    }
    
    /* Eliminar cualquier acción o cursor al pasar sobre las imágenes */
    .element-container:has(img) {
        pointer-events: none;
    }
    </style>
    """, unsafe_allow_html=True)

def admin_console_page():
    """Admin console page for managing frameworks and compass evaluations."""
    # Check if user is already authenticated
    if not st.session_state.get("admin_authenticated", False):
        show_login_page()
        return
    
    # Create a header with login info and logout button
    st.markdown('<h1 class="main-header">Sherpa Admin Console</h1>', unsafe_allow_html=True)
    
    # Logout button
    if st.button("Cerrar Sesión", type="secondary"):
        st.session_state["admin_authenticated"] = False
        st.rerun()
    
    st.markdown(f"Sesión iniciada como: **admin**")
    st.markdown("---")
    
    # Add custom CSS for admin console
    st.markdown("""
    <style>
    .admin-section {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .admin-section h2 {
        margin-top: 0;
        color: #333;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main admin tabs - separate Frameworks and Compass
    admin_tabs = st.tabs(["Frameworks Management", "Compass Management"])
    
    #########################################
    # FRAMEWORKS MANAGEMENT TAB
    #########################################
    with admin_tabs[0]:
        st.markdown("# Frameworks Management")
        st.markdown("Create, edit and manage evaluation frameworks that define criteria for subnet assessment.")
        
        # Load all frameworks at the start
        all_frameworks = load_frameworks()
        framework_names = [f['name'] for f in all_frameworks]
        
        if not framework_names:
            st.warning("No frameworks found. Use the 'Create Framework' section to create your first framework.")
            # Add a default framework for convenience
            framework_names = ["Default Framework"]
        
        framework_section = st.selectbox(
            "Choose a section", 
            ["View Frameworks", "Create Framework", "Edit Framework", "Import/Export Framework", "Delete Framework"]
        )
        
        if framework_section == "View Frameworks":
            st.markdown("## Available Frameworks")
            
            # Función de utilidad para actualizar el estado activo de un framework
            def update_framework_active_status(framework_path, is_active):
                try:
                    # Cargar el framework desde el archivo
                    with open(framework_path, 'r') as f:
                        framework_data = json.load(f)
                    
                    # Actualizar el estado activo
                    framework_data['active'] = is_active
                    
                    # Guardar el framework actualizado
                    with open(framework_path, 'w') as f:
                        json.dump(framework_data, f, indent=4)
                    
                    return True
                except Exception as e:
                    print(f"Error updating framework active status: {str(e)}")
                    return False
            
            for idx, framework in enumerate(all_frameworks):
                # Preparar el título con indicador de estado
                is_active = framework.get('active', True)
                status_indicator = "🟢 " if is_active else "🔴 "
                framework_title = f"{status_indicator}{framework['name']}"
                
                # Generar un ID único para el checkbox
                checkbox_id = f"active_toggle_{idx}"
                
                # Crear un expander por framework
                with st.expander(framework_title):
                    # Mostrar toda la información del framework
                    st.json(framework)
                    
                    # Añadir el toggle para habilitar/deshabilitar
                    if st.checkbox(
                        "Habilitado para usuarios", 
                        value=is_active,
                        key=checkbox_id,
                        help="Activa/desactiva la visibilidad de este framework para los usuarios en la página de selección"
                    ):
                        # Si el checkbox está marcado y el framework estaba deshabilitado
                        if not is_active:
                            if update_framework_active_status(framework['_filepath'], True):
                                st.success(f"Framework '{framework['name']}' habilitado correctamente.")
                                st.rerun()  # Recargar la página para reflejar el cambio
                    else:
                        # Si el checkbox está desmarcado y el framework estaba habilitado
                        if is_active:
                            if update_framework_active_status(framework['_filepath'], False):
                                st.warning(f"Framework '{framework['name']}' deshabilitado. No será visible para los usuarios.")
                                st.rerun()  # Recargar la página para reflejar el cambio
        
        elif framework_section == "Create Framework":
            st.markdown("## Create New Framework")
            
            # Framework basic info
            framework_name = st.text_input("Framework Name", "New Framework")
            framework_description = st.text_area("Framework Description", "A new evaluation framework for subnet classification")
            
            # Use tabs for different criteria sections
            criteria_tabs = st.tabs(["Service Criteria", "Research Criteria", "Intelligence Criteria", "Resource Criteria", "Additional Criteria"])
            
            # Default criteria from existing functions
            default_criteria = get_evaluation_criteria()
            default_additional = get_additional_evaluation_criteria()
            
            # Service criteria tab
            with criteria_tabs[0]:
                st.markdown("### Service-Oriented Criteria")
                
                # Usar session_state para mantener el estado de los criterios entre renders
                if 'service_criteria' not in st.session_state:
                    st.session_state.service_criteria = {}
                    # Clone the default criteria
                    for key, description in default_criteria['service'].items():
                        st.session_state.service_criteria[key] = description
                
                # Función para añadir nuevo criterio
                def add_service_criterion():
                    new_key = f"custom_service_{len(st.session_state.service_criteria) + 1}"
                    st.session_state.service_criteria[new_key] = ""
                    st.rerun()
                
                # Mostrar los criterios existentes con opción de eliminación
                service_criteria = {}  # Este diccionario almacenará los valores actualizados
                keys_to_delete = []
                
                for key in list(st.session_state.service_criteria.keys()):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        new_description = st.text_input(
                            f"Service: {key}", 
                            value=st.session_state.service_criteria[key], 
                            key=f"new_service_{key}"
                        )
                        service_criteria[key] = new_description
                    with col2:
                        if st.button("🗑️", key=f"delete_service_{key}"):
                            keys_to_delete.append(key)
                
                # Eliminar los criterios marcados para eliminación
                for key in keys_to_delete:
                    if key in st.session_state.service_criteria:
                        del st.session_state.service_criteria[key]
                    st.rerun()
                
                # Actualizar los valores en session_state
                for key, value in service_criteria.items():
                    st.session_state.service_criteria[key] = value
                
                # Option to add new criteria
                st.button("Add New Service Criterion", key="add_service", on_click=add_service_criterion)
            
            # Research criteria tab
            with criteria_tabs[1]:
                st.markdown("### Research-Oriented Criteria")
                
                # Usar session_state para mantener el estado de los criterios entre renders
                if 'research_criteria' not in st.session_state:
                    st.session_state.research_criteria = {}
                    # Clone the default criteria
                    for key, description in default_criteria['research'].items():
                        st.session_state.research_criteria[key] = description
                
                # Función para añadir nuevo criterio
                def add_research_criterion():
                    new_key = f"custom_research_{len(st.session_state.research_criteria) + 1}"
                    st.session_state.research_criteria[new_key] = ""
                    st.rerun()
                
                # Mostrar los criterios existentes con opción de eliminación
                research_criteria = {}  # Este diccionario almacenará los valores actualizados
                keys_to_delete = []
                
                for key in list(st.session_state.research_criteria.keys()):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        new_description = st.text_input(
                            f"Research: {key}", 
                            value=st.session_state.research_criteria[key], 
                            key=f"new_research_{key}"
                        )
                        research_criteria[key] = new_description
                    with col2:
                        if st.button("🗑️", key=f"delete_research_{key}"):
                            keys_to_delete.append(key)
                
                # Eliminar los criterios marcados para eliminación
                for key in keys_to_delete:
                    if key in st.session_state.research_criteria:
                        del st.session_state.research_criteria[key]
                    st.rerun()
                
                # Actualizar los valores en session_state
                for key, value in research_criteria.items():
                    st.session_state.research_criteria[key] = value
                
                # Option to add new criteria
                st.button("Add New Research Criterion", key="add_research", on_click=add_research_criterion)
            
            # Intelligence criteria tab
            with criteria_tabs[2]:
                st.markdown("### Intelligence-Oriented Criteria")
                
                # Usar session_state para mantener el estado de los criterios entre renders
                if 'intelligence_criteria' not in st.session_state:
                    st.session_state.intelligence_criteria = {}
                    # Clone the default criteria
                    for key, description in default_criteria['intelligence'].items():
                        st.session_state.intelligence_criteria[key] = description
                
                # Función para añadir nuevo criterio
                def add_intelligence_criterion():
                    new_key = f"custom_intelligence_{len(st.session_state.intelligence_criteria) + 1}"
                    st.session_state.intelligence_criteria[new_key] = ""
                    st.rerun()
                
                # Mostrar los criterios existentes con opción de eliminación
                intelligence_criteria = {}  # Este diccionario almacenará los valores actualizados
                keys_to_delete = []
                
                for key in list(st.session_state.intelligence_criteria.keys()):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        new_description = st.text_input(
                            f"Intelligence: {key}", 
                            value=st.session_state.intelligence_criteria[key], 
                            key=f"new_intelligence_{key}"
                        )
                        intelligence_criteria[key] = new_description
                    with col2:
                        if st.button("🗑️", key=f"delete_intelligence_{key}"):
                            keys_to_delete.append(key)
                
                # Eliminar los criterios marcados para eliminación
                for key in keys_to_delete:
                    if key in st.session_state.intelligence_criteria:
                        del st.session_state.intelligence_criteria[key]
                    st.rerun()
                
                # Actualizar los valores en session_state
                for key, value in intelligence_criteria.items():
                    st.session_state.intelligence_criteria[key] = value
                
                # Option to add new criteria
                st.button("Add New Intelligence Criterion", key="add_intelligence", on_click=add_intelligence_criterion)
            
            # Resource criteria tab
            with criteria_tabs[3]:
                st.markdown("### Resource-Oriented Criteria")
                
                # Usar session_state para mantener el estado de los criterios entre renders
                if 'resource_criteria' not in st.session_state:
                    st.session_state.resource_criteria = {}
                    # Clone the default criteria
                    for key, description in default_criteria['resource'].items():
                        st.session_state.resource_criteria[key] = description
                
                # Función para añadir nuevo criterio
                def add_resource_criterion():
                    new_key = f"custom_resource_{len(st.session_state.resource_criteria) + 1}"
                    st.session_state.resource_criteria[new_key] = ""
                    st.rerun()
                
                # Mostrar los criterios existentes con opción de eliminación
                resource_criteria = {}  # Este diccionario almacenará los valores actualizados
                keys_to_delete = []
                
                for key in list(st.session_state.resource_criteria.keys()):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        new_description = st.text_input(
                            f"Resource: {key}", 
                            value=st.session_state.resource_criteria[key], 
                            key=f"new_resource_{key}"
                        )
                        resource_criteria[key] = new_description
                    with col2:
                        if st.button("🗑️", key=f"delete_resource_{key}"):
                            keys_to_delete.append(key)
                
                # Eliminar los criterios marcados para eliminación
                for key in keys_to_delete:
                    if key in st.session_state.resource_criteria:
                        del st.session_state.resource_criteria[key]
                    st.rerun()
                
                # Actualizar los valores en session_state
                for key, value in resource_criteria.items():
                    st.session_state.resource_criteria[key] = value
                
                # Option to add new criteria
                st.button("Add New Resource Criterion", key="add_resource", on_click=add_resource_criterion)
            
            # Additional criteria tab
            with criteria_tabs[4]:
                st.markdown("### Additional Criteria")
                
                # Usar session_state para mantener el estado de los criterios entre renders
                if 'additional_criteria' not in st.session_state:
                    st.session_state.additional_criteria = {}
                    # Clone the default criteria
                    for key, data in default_additional.items():
                        st.session_state.additional_criteria[key] = data.copy()
                
                # Función para añadir nuevo criterio adicional
                def add_additional_criterion():
                    new_key = f"custom_additional_{len(st.session_state.additional_criteria) + 1}"
                    st.session_state.additional_criteria[new_key] = {
                        "description": "",
                        "weight": 0.5,
                        "type": "positive"
                    }
                    st.rerun()
                
                # Mostrar los criterios existentes con opción de eliminación
                additional_criteria = {}  # Este diccionario almacenará los valores actualizados
                keys_to_delete = []
                
                for key in list(st.session_state.additional_criteria.keys()):
                    data = st.session_state.additional_criteria[key]
                    
                    # Crear un header para el criterio
                    header_col1, header_col2 = st.columns([5, 1])
                    with header_col1:
                        st.markdown(f"#### {data.get('description', '')}")
                    with header_col2:
                        if st.button("🗑️", key=f"delete_additional_{key}"):
                            keys_to_delete.append(key)
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        new_description = st.text_input(
                            f"Description", 
                            value=data.get('description', ''), 
                            key=f"new_additional_desc_{key}"
                        )
                    
                    with col2:
                        new_weight = st.number_input(
                            "Weight",
                            min_value=0.1,
                            max_value=3.0,  # Cambiado rango a 3.0
                            value=data.get("weight", 0.5),
                            step=0.1,
                            key=f"new_additional_weight_{key}"
                        )
                    
                    with col3:
                        new_type = st.selectbox(
                            "Type",
                            ["positive", "negative", "bidirectional"],
                            index=["positive", "negative", "bidirectional"].index(data.get("type", "positive")),
                            key=f"new_additional_type_{key}"
                        )
                    
                    additional_criteria[key] = {
                        "description": new_description,
                        "weight": new_weight,
                        "type": new_type
                    }
                    
                    st.markdown("---")
                
                # Eliminar los criterios marcados para eliminación
                for key in keys_to_delete:
                    if key in st.session_state.additional_criteria:
                        del st.session_state.additional_criteria[key]
                    st.rerun()
                
                # Actualizar los valores en session_state
                for key, data in additional_criteria.items():
                    st.session_state.additional_criteria[key] = data
                
                # Option to add new additional criterion
                st.button("Add New Additional Criterion", key="add_additional", on_click=add_additional_criterion)
            
            # Save button for new framework
            if st.button("Save New Framework", key="save_new_framework"):
                # Create combined criteria
                all_criteria = {
                    "service": service_criteria,
                    "research": research_criteria,
                    "intelligence": intelligence_criteria,
                    "resource": resource_criteria
                }
                
                # Create complete framework data
                new_framework = {
                    "name": framework_name,
                    "description": framework_description,
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "criteria": all_criteria,
                    "additional_criteria": additional_criteria
                }
                
                # Save the framework to a file
                success, result = save_framework(new_framework)
                
                if success:
                    st.success(f"Framework '{framework_name}' created successfully!")
                    # Force a reload of the framework list
                    st.rerun()
                else:
                    st.error(f"Error creating framework: {result}")
        
        elif framework_section == "Edit Framework":
            st.markdown("## Edit Existing Framework")
            
            if not all_frameworks:
                st.warning("No frameworks available to edit.")
            else:
                # Select a framework to edit
                selected_framework_name = st.selectbox("Select Framework to Edit", framework_names)
                
                # Find the selected framework
                selected_framework = next((f for f in all_frameworks if f['name'] == selected_framework_name), None)
                
                if selected_framework:
                    # Framework basic info
                    framework_name = st.text_input("Framework Name", selected_framework.get('name', ''))
                    framework_description = st.text_area("Framework Description", selected_framework.get('description', ''))
                    
                    # Use tabs for different criteria sections
                    criteria_tabs = st.tabs(["Service Criteria", "Research Criteria", "Intelligence Criteria", "Resource Criteria", "Additional Criteria"])
                    
                    # Get criteria from the selected framework
                    framework_criteria = selected_framework.get('criteria', {})
                    
                    # Service criteria tab
                    with criteria_tabs[0]:
                        st.markdown("### Service-Oriented Criteria")
                        
                        # Usar session_state para mantener el estado de los criterios entre renders
                        # Inicializar en el primer render con los datos del framework seleccionado
                        service_dict_key = f"edit_service_dict_{selected_framework_name}"
                        if service_dict_key not in st.session_state:
                            st.session_state[service_dict_key] = {}
                            # Clone the framework criteria
                            service_dict = framework_criteria.get('service', {})
                            for key, description in service_dict.items():
                                st.session_state[service_dict_key][key] = description

                        # Función para añadir nuevo criterio
                        def add_service_criterion_edit():
                            new_key = f"custom_service_{len(st.session_state[service_dict_key]) + 1}"
                            st.session_state[service_dict_key][new_key] = ""
                            st.rerun()
                        
                        # Mostrar los criterios existentes con opción de eliminación
                        service_criteria = {}  # Este diccionario almacenará los valores actualizados
                        keys_to_delete = []
                        
                        for key in list(st.session_state[service_dict_key].keys()):
                            col1, col2 = st.columns([5, 1])
                            with col1:
                                new_description = st.text_input(
                                    f"Service: {key}", 
                                    value=st.session_state[service_dict_key][key], 
                                    key=f"edit_service_{key}"
                                )
                                service_criteria[key] = new_description
                            with col2:
                                if st.button("🗑️", key=f"delete_edit_service_{key}"):
                                    keys_to_delete.append(key)
                        
                        # Eliminar los criterios marcados para eliminación
                        for key in keys_to_delete:
                            if key in st.session_state[service_dict_key]:
                                del st.session_state[service_dict_key][key]
                            st.rerun()
                        
                        # Actualizar los valores en session_state
                        for key, value in service_criteria.items():
                            st.session_state[service_dict_key][key] = value
                        
                        # Option to add new criteria
                        st.button("Add New Service Criterion", key="edit_add_service", on_click=add_service_criterion_edit)
                    
                    # Research criteria tab
                    with criteria_tabs[1]:
                        st.markdown("### Research-Oriented Criteria")
                        
                        # Usar session_state para mantener el estado de los criterios entre renders
                        research_dict_key = f"edit_research_dict_{selected_framework_name}"
                        if research_dict_key not in st.session_state:
                            st.session_state[research_dict_key] = {}
                            # Clone the framework criteria
                            research_dict = framework_criteria.get('research', {})
                            for key, description in research_dict.items():
                                st.session_state[research_dict_key][key] = description

                        # Función para añadir nuevo criterio
                        def add_research_criterion_edit():
                            new_key = f"custom_research_{len(st.session_state[research_dict_key]) + 1}"
                            st.session_state[research_dict_key][new_key] = ""
                            st.rerun()
                        
                        # Mostrar los criterios existentes con opción de eliminación
                        research_criteria = {}  # Este diccionario almacenará los valores actualizados
                        keys_to_delete = []
                        
                        for key in list(st.session_state[research_dict_key].keys()):
                            col1, col2 = st.columns([5, 1])
                            with col1:
                                new_description = st.text_input(
                                    f"Research: {key}", 
                                    value=st.session_state[research_dict_key][key], 
                                    key=f"edit_research_{key}"
                                )
                                research_criteria[key] = new_description
                            with col2:
                                if st.button("🗑️", key=f"delete_edit_research_{key}"):
                                    keys_to_delete.append(key)
                        
                        # Eliminar los criterios marcados para eliminación
                        for key in keys_to_delete:
                            if key in st.session_state[research_dict_key]:
                                del st.session_state[research_dict_key][key]
                            st.rerun()
                        
                        # Actualizar los valores en session_state
                        for key, value in research_criteria.items():
                            st.session_state[research_dict_key][key] = value
                        
                        # Option to add new criteria
                        st.button("Add New Research Criterion", key="edit_add_research", on_click=add_research_criterion_edit)
                    
                    # Intelligence criteria tab
                    with criteria_tabs[2]:
                        st.markdown("### Intelligence-Oriented Criteria")
                        
                        # Usar session_state para mantener el estado de los criterios entre renders
                        intelligence_dict_key = f"edit_intelligence_dict_{selected_framework_name}"
                        if intelligence_dict_key not in st.session_state:
                            st.session_state[intelligence_dict_key] = {}
                            # Clone the framework criteria
                            intelligence_dict = framework_criteria.get('intelligence', {})
                            for key, description in intelligence_dict.items():
                                st.session_state[intelligence_dict_key][key] = description

                        # Función para añadir nuevo criterio
                        def add_intelligence_criterion_edit():
                            new_key = f"custom_intelligence_{len(st.session_state[intelligence_dict_key]) + 1}"
                            st.session_state[intelligence_dict_key][new_key] = ""
                            st.rerun()
                        
                        # Mostrar los criterios existentes con opción de eliminación
                        intelligence_criteria = {}  # Este diccionario almacenará los valores actualizados
                        keys_to_delete = []
                        
                        for key in list(st.session_state[intelligence_dict_key].keys()):
                            col1, col2 = st.columns([5, 1])
                            with col1:
                                new_description = st.text_input(
                                    f"Intelligence: {key}", 
                                    value=st.session_state[intelligence_dict_key][key], 
                                    key=f"edit_intelligence_{key}"
                                )
                                intelligence_criteria[key] = new_description
                            with col2:
                                if st.button("🗑️", key=f"delete_edit_intelligence_{key}"):
                                    keys_to_delete.append(key)
                        
                        # Eliminar los criterios marcados para eliminación
                        for key in keys_to_delete:
                            if key in st.session_state[intelligence_dict_key]:
                                del st.session_state[intelligence_dict_key][key]
                            st.rerun()
                        
                        # Actualizar los valores en session_state
                        for key, value in intelligence_criteria.items():
                            st.session_state[intelligence_dict_key][key] = value
                        
                        # Option to add new criteria
                        st.button("Add New Intelligence Criterion", key="edit_add_intelligence", on_click=add_intelligence_criterion_edit)
                    
                    # Resource criteria tab
                    with criteria_tabs[3]:
                        st.markdown("### Resource-Oriented Criteria")
                        
                        # Usar session_state para mantener el estado de los criterios entre renders
                        resource_dict_key = f"edit_resource_dict_{selected_framework_name}"
                        if resource_dict_key not in st.session_state:
                            st.session_state[resource_dict_key] = {}
                            # Clone the framework criteria
                            resource_dict = framework_criteria.get('resource', {})
                            for key, description in resource_dict.items():
                                st.session_state[resource_dict_key][key] = description

                        # Función para añadir nuevo criterio
                        def add_resource_criterion_edit():
                            new_key = f"custom_resource_{len(st.session_state[resource_dict_key]) + 1}"
                            st.session_state[resource_dict_key][new_key] = ""
                            st.rerun()
                        
                        # Mostrar los criterios existentes con opción de eliminación
                        resource_criteria = {}  # Este diccionario almacenará los valores actualizados
                        keys_to_delete = []
                        
                        for key in list(st.session_state[resource_dict_key].keys()):
                            col1, col2 = st.columns([5, 1])
                            with col1:
                                new_description = st.text_input(
                                    f"Resource: {key}", 
                                    value=st.session_state[resource_dict_key][key], 
                                    key=f"edit_resource_{key}"
                                )
                                resource_criteria[key] = new_description
                            with col2:
                                if st.button("🗑️", key=f"delete_edit_resource_{key}"):
                                    keys_to_delete.append(key)
                        
                        # Eliminar los criterios marcados para eliminación
                        for key in keys_to_delete:
                            if key in st.session_state[resource_dict_key]:
                                del st.session_state[resource_dict_key][key]
                            st.rerun()
                        
                        # Actualizar los valores en session_state
                        for key, value in resource_criteria.items():
                            st.session_state[resource_dict_key][key] = value
                        
                        # Option to add new criteria
                        st.button("Add New Resource Criterion", key="edit_add_resource", on_click=add_resource_criterion_edit)
                    
                    # Additional criteria tab
                    with criteria_tabs[4]:
                        st.markdown("### Additional Criteria")
                        
                        # Usar session_state para mantener el estado de los criterios entre renders
                        additional_dict_key = f"edit_additional_dict_{selected_framework_name}"
                        if additional_dict_key not in st.session_state:
                            st.session_state[additional_dict_key] = {}
                            # Clone the framework additional criteria
                            additional_dict = selected_framework.get('additional_criteria', {})
                            for key, data in additional_dict.items():
                                st.session_state[additional_dict_key][key] = data.copy()
                        
                        # Función para añadir nuevo criterio adicional
                        def add_additional_criterion_edit():
                            new_key = f"custom_additional_{len(st.session_state[additional_dict_key]) + 1}"
                            st.session_state[additional_dict_key][new_key] = {
                                "description": "",
                                "weight": 0.5,
                                "type": "positive"
                            }
                            st.rerun()
                        
                        # Mostrar los criterios existentes con opción de eliminación
                        additional_criteria = {}  # Este diccionario almacenará los valores actualizados
                        keys_to_delete = []
                        
                        for key in list(st.session_state[additional_dict_key].keys()):
                            data = st.session_state[additional_dict_key][key]
                            
                            # Crear un header para el criterio
                            header_col1, header_col2 = st.columns([5, 1])
                            with header_col1:
                                st.markdown(f"#### {data.get('description', '')}")
                            with header_col2:
                                if st.button("🗑️", key=f"delete_edit_additional_{key}"):
                                    keys_to_delete.append(key)
                            
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                new_description = st.text_input(
                                    f"Description", 
                                    value=data.get('description', ''), 
                                    key=f"edit_additional_desc_{key}"
                                )
                            
                            with col2:
                                new_weight = st.number_input(
                                    "Weight",
                                    min_value=0.1,
                                    max_value=3.0,  # Cambiado rango a 3.0
                                    value=data.get("weight", 0.5),
                                    step=0.1,
                                    key=f"edit_additional_weight_{key}"
                                )
                            
                            with col3:
                                new_type = st.selectbox(
                                    "Type",
                                    ["positive", "negative", "bidirectional"],
                                    index=["positive", "negative", "bidirectional"].index(data.get("type", "positive")),
                                    key=f"edit_additional_type_{key}"
                                )
                            
                            additional_criteria[key] = {
                                "description": new_description,
                                "weight": new_weight,
                                "type": new_type
                            }
                            
                            st.markdown("---")
                            
                        # Eliminar los criterios marcados para eliminación
                        for key in keys_to_delete:
                            if key in st.session_state[additional_dict_key]:
                                del st.session_state[additional_dict_key][key]
                            st.rerun()
                        
                        # Actualizar los valores en session_state
                        for key, data in additional_criteria.items():
                            st.session_state[additional_dict_key][key] = data
                        
                        # Option to add new additional criterion
                        st.button("Add New Additional Criterion", key="edit_add_additional", on_click=add_additional_criterion_edit)
                    
                    # Save button for edited framework
                    if st.button("Save Framework Changes", key="save_framework_changes"):
                        # Create combined criteria
                        all_criteria = {
                            "service": service_criteria,
                            "research": research_criteria,
                            "intelligence": intelligence_criteria,
                            "resource": resource_criteria
                        }
                        
                        # Update framework data
                        updated_framework = selected_framework.copy()
                        updated_framework["name"] = framework_name
                        updated_framework["description"] = framework_description
                        updated_framework["updated_at"] = datetime.now().isoformat()
                        updated_framework["criteria"] = all_criteria
                        updated_framework["additional_criteria"] = additional_criteria
                        
                        # Save the updated framework to the same file
                        filepath = selected_framework.get('_filepath')
                        success, result = save_framework(updated_framework, filepath)
                        
                        if success:
                            st.success(f"Framework '{framework_name}' updated successfully!")
                            # Force a reload of the framework list
                            st.rerun()
                        else:
                            st.error(f"Error updating framework: {result}")
        
        elif framework_section == "Import/Export Framework":
            st.markdown("## Import/Export Framework")
            
            import_export_tabs = st.tabs(["Export Framework", "Import Framework"])
            
            with import_export_tabs[0]:
                st.markdown("### Export Framework")
                
                if not all_frameworks:
                    st.warning("No frameworks available to export.")
                else:
                    # Select a framework to export
                    export_framework_name = st.selectbox("Select Framework to Export", framework_names, key="export_framework")
                    
                    # Find the selected framework
                    export_framework = next((f for f in all_frameworks if f['name'] == export_framework_name), None)
                    
                    if export_framework and st.button("Prepare for Export", key="prepare_export"):
                        # Remove internal filepath before exporting
                        export_data = export_framework.copy()
                        if '_filepath' in export_data:
                            del export_data['_filepath']
                        
                        # Convert to JSON
                        framework_json = json.dumps(export_data, indent=4)
                        
                        # Create a download button for the JSON file
                        st.download_button(
                            label="Download Framework JSON",
                            data=framework_json,
                            file_name=f"{export_framework_name.lower().replace(' ', '_')}.json",
                            mime="application/json"
                        )
                        
                        st.success(f"Framework '{export_framework_name}' ready for download.")
            
            with import_export_tabs[1]:
                st.markdown("### Import Framework")
                
                uploaded_file = st.file_uploader("Upload Framework JSON File", type="json")
                
                if uploaded_file is not None:
                    try:
                        # Load the uploaded file
                        framework_data = json.load(uploaded_file)
                        
                        # Display a preview
                        st.markdown("#### Framework Preview:")
                        st.json(framework_data)
                        
                        # Confirm import
                        if st.button("Confirm Import", key="confirm_import"):
                            # Add timestamps if missing
                            if 'created_at' not in framework_data:
                                framework_data['created_at'] = datetime.now().isoformat()
                            framework_data['updated_at'] = datetime.now().isoformat()
                            
                            # Save the framework
                            success, result = save_framework(framework_data)
                            
                            if success:
                                st.success(f"Framework '{framework_data.get('name', 'Imported')}' imported successfully!")
                                # Force a reload of the framework list
                                st.rerun()
                            else:
                                st.error(f"Error importing framework: {result}")
                            
                    except Exception as e:
                        st.error(f"Error importing framework: {str(e)}")
        
        elif framework_section == "Delete Framework":
            st.markdown("## Delete Framework")
            
            if not all_frameworks:
                st.warning("No frameworks available to delete.")
            else:
                # Select a framework to delete
                delete_framework_name = st.selectbox("Select Framework to Delete", framework_names, key="delete_framework")
                
                # Find the selected framework
                delete_framework = next((f for f in all_frameworks if f['name'] == delete_framework_name), None)
                
                if delete_framework:
                    st.warning(f"Are you sure you want to delete the framework '{delete_framework_name}'? This action cannot be undone.")
                    
                    # Confirm deletion
                    if st.button("Confirm Deletion", key="confirm_delete"):
                        if '_filepath' in delete_framework:
                            # Delete the framework file
                            success = delete_framework(delete_framework['_filepath'])
                            
                            if success:
                                st.success(f"Framework '{delete_framework_name}' deleted successfully!")
                                # Force a reload of the framework list
                                st.rerun()
                            else:
                                st.error(f"Error deleting framework.")
                        else:
                            st.error(f"Framework file path not found.")
    
    #########################################
    # COMPASS MANAGEMENT TAB
    #########################################
    with admin_tabs[1]:
        st.markdown("# Compass Management")
        st.markdown("Create, edit and manage compass evaluations (subnet assessments).")
        
        # Load all compasses and frameworks
        all_compasses = load_compasses()
        all_frameworks = load_frameworks()
        
        compass_names = [c['name'] for c in all_compasses]
        framework_names = [f['name'] for f in all_frameworks]
        
        if not framework_names:
            st.warning("No frameworks found. Please create a framework first before creating compass assessments.")
            return
        
        compass_section = st.selectbox(
            "Choose a section", 
            ["View Compass Evaluations", "Create Compass Evaluation", "Edit Compass Evaluation", "Export Compass Evaluation", "Delete Compass Evaluation"]
        )
        
        if compass_section == "View Compass Evaluations":
            st.markdown("## Available Compass Evaluations")
            
            if not all_compasses:
                st.info("No compass evaluations found.")
            else:
                for compass in all_compasses:
                    with st.expander(f"{compass['name']}"):
                        st.markdown(f"**Framework:** {compass.get('framework', 'N/A')}")
                        st.markdown(f"**Description:** {compass.get('description', 'N/A')}")
                        st.markdown(f"**Total Score:** {compass.get('total_score', 0)}")
                        st.markdown(f"**Tier:** {compass.get('tier', 'N/A')}")
                        
                        if st.button("View Full Details", key=f"view_details_{compass.get('_filepath', '')}"):
                            st.json(compass)
        
        elif compass_section == "Create Compass Evaluation":
            st.markdown("## Create New Compass Evaluation")
            
            # Basic info
            compass_name = st.text_input("Subnet Name", "New Subnet")
            compass_uid = st.text_input("Subnet UID (optional)", "")
            compass_description = st.text_area("Description", "A new subnet evaluation")
            
            # Select a framework
            selected_framework_name = st.selectbox("Select Framework", framework_names)
            
            # Find the selected framework
            selected_framework = next((f for f in all_frameworks if f['name'] == selected_framework_name), None)
            
            if selected_framework:
                st.markdown("### Score this subnet based on the framework criteria")
                
                # Use tabs for different criteria sections
                scoring_tabs = st.tabs(["Service Scores", "Research Scores", "Intelligence Scores", "Resource Scores", "Additional Scores"])
                
                # Get criteria from the selected framework
                framework_criteria = selected_framework.get('criteria', {})
                additional_criteria = selected_framework.get('additional_criteria', {})
                
                # Service scores tab
                with scoring_tabs[0]:
                    st.markdown("### Service-Oriented Scores")
                    service_scores = {}
                    
                    service_dict = framework_criteria.get('service', {})
                    for key, description in service_dict.items():
                        score = st.slider(
                            f"{description} ({key})",
                            min_value=0.0,
                            max_value=3.0,
                            value=0.5,
                            step=0.1,
                            key=f"new_score_service_{key}"
                        )
                        service_scores[key] = score
                
                # Research scores tab
                with scoring_tabs[1]:
                    st.markdown("### Research-Oriented Scores")
                    research_scores = {}
                    
                    research_dict = framework_criteria.get('research', {})
                    for key, description in research_dict.items():
                        score = st.slider(
                            f"{description} ({key})",
                            min_value=0.0,
                            max_value=3.0,
                            value=0.5,
                            step=0.1,
                            key=f"new_score_research_{key}"
                        )
                        research_scores[key] = score
                
                # Intelligence scores tab
                with scoring_tabs[2]:
                    st.markdown("### Intelligence-Oriented Scores")
                    intelligence_scores = {}
                    
                    intelligence_dict = framework_criteria.get('intelligence', {})
                    for key, description in intelligence_dict.items():
                        score = st.slider(
                            f"{description} ({key})",
                            min_value=0.0,
                            max_value=3.0,
                            value=0.5,
                            step=0.1,
                            key=f"new_score_intelligence_{key}"
                        )
                        intelligence_scores[key] = score
                
                # Resource scores tab
                with scoring_tabs[3]:
                    st.markdown("### Resource-Oriented Scores")
                    resource_scores = {}
                    
                    resource_dict = framework_criteria.get('resource', {})
                    for key, description in resource_dict.items():
                        score = st.slider(
                            f"{description} ({key})",
                            min_value=0.0,
                            max_value=3.0,
                            value=0.5,
                            step=0.1,
                            key=f"new_score_resource_{key}"
                        )
                        resource_scores[key] = score
                
                # Additional scores tab
                with scoring_tabs[4]:
                    st.markdown("### Additional Criteria Scores")
                    additional_scores = {}
                    additional_weights = {}
                    
                    for key, data in additional_criteria.items():
                        description = data.get('description', '')
                        weight = data.get('weight', 0.5)
                        score_type = data.get('type', 'positive')
                        
                        # Store the weight
                        additional_weights[key] = weight
                        
                        # Calculate the score range based on the criteria type
                        if score_type == 'positive':
                            min_val, max_val, default_val = 0.0, 1.0, 0.5
                        elif score_type == 'negative':
                            min_val, max_val, default_val = -1.0, 0.0, -0.5
                        else:  # bidirectional
                            min_val, max_val, default_val = -1.0, 1.0, 0.0
                        
                        score = st.slider(
                            f"{description} ({key}, type: {score_type}, weight: {weight})",
                            min_value=min_val,
                            max_value=max_val,
                            value=default_val,
                            step=0.1,
                            key=f"new_score_additional_{key}"
                        )
                        additional_scores[key] = score
                
                # Calculate scores
                scores = calculate_scores(
                    service_scores,
                    research_scores,
                    intelligence_scores,
                    resource_scores,
                    additional_scores,
                    additional_weights
                )
                
                # Display calculated scores
                st.markdown("### Calculated Scores")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Service-Research Score", f"{scores.get('service_research_score', (0,0))}")
                with col2:
                    st.metric("Intelligence-Resource Score", f"{scores.get('intelligence_resource_score', (0,0))}")
                with col3:
                    st.metric("Total Score", f"{scores.get('total_score', 0):.2f}")
                    st.metric("Tier", scores.get('tier', 'N/A'))
                
                # Save button for new compass
                if st.button("Save Compass Evaluation", key="save_new_compass"):
                    # Create compass data
                    compass_data = {
                        "name": compass_name,
                        "uid": compass_uid,
                        "description": compass_description,
                        "framework": selected_framework_name,
                        "framework_path": selected_framework.get('_filepath', ''),
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                        "service_oriented_scores": service_scores,
                        "research_oriented_scores": research_scores,
                        "intelligence_oriented_scores": intelligence_scores,
                        "resource_oriented_scores": resource_scores,
                        "additional_criteria_scores": {
                            "scores": additional_scores,
                            "weights": additional_weights
                        },
                        "service_research_score": scores.get('service_research_score', (0,0)),
                        "intelligence_resource_score": scores.get('intelligence_resource_score', (0,0)),
                        "total_score": scores.get('total_score', 0),
                        "tier": scores.get('tier', 'N/A')
                    }
                    
                    # Save the compass
                    success, result = save_compass(compass_data)
                    
                    if success:
                        st.success(f"Compass evaluation '{compass_name}' created successfully!")
                        # Force a reload
                        st.rerun()
                    else:
                        st.error(f"Error creating compass evaluation: {result}")
        
        elif compass_section == "Edit Compass Evaluation":
            st.markdown("## Edit Compass Evaluation")
            
            if not all_compasses:
                st.warning("No compass evaluations available to edit.")
            else:
                # Select a compass to edit
                selected_compass_name = st.selectbox("Select Compass to Edit", compass_names)
                
                # Find the selected compass
                selected_compass = next((c for c in all_compasses if c['name'] == selected_compass_name), None)
                
                if selected_compass:
                    # Basic info
                    compass_name = st.text_input("Subnet Name", selected_compass.get('name', ''))
                    compass_uid = st.text_input("Subnet UID", selected_compass.get('uid', ''))
                    compass_description = st.text_area("Description", selected_compass.get('description', ''))
                    
                    # Framework information (read-only)
                    framework_name = selected_compass.get('framework', 'Unknown Framework')
                    st.markdown(f"**Framework:** {framework_name}")
                    
                    # Use tabs for different criteria sections
                    scoring_tabs = st.tabs(["Service Scores", "Research Scores", "Intelligence Scores", "Resource Scores", "Additional Scores"])
                    
                    # Get current scores
                    service_scores = selected_compass.get('service_oriented_scores', {})
                    research_scores = selected_compass.get('research_oriented_scores', {})
                    intelligence_scores = selected_compass.get('intelligence_oriented_scores', {})
                    resource_scores = selected_compass.get('resource_oriented_scores', {})
                    additional_criteria = selected_compass.get('additional_criteria_scores', {})
                    additional_scores = additional_criteria.get('scores', {})
                    additional_weights = additional_criteria.get('weights', {})
                    
                    # Find the framework to get descriptions
                    framework = next((f for f in all_frameworks if f['name'] == framework_name), None)
                    framework_criteria = {}
                    framework_additional = {}
                    
                    if framework:
                        framework_criteria = framework.get('criteria', {})
                        framework_additional = framework.get('additional_criteria', {})
                    
                    # Service scores tab
                    with scoring_tabs[0]:
                        st.markdown("### Service-Oriented Scores")
                        updated_service_scores = {}
                        
                        for key, score in service_scores.items():
                            description = framework_criteria.get('service', {}).get(key, key)
                            updated_score = st.slider(
                                f"{description} ({key})",
                                min_value=0.0,
                                max_value=3.0,
                                value=float(score),
                                step=0.1,
                                key=f"edit_score_service_{key}"
                            )
                            updated_service_scores[key] = updated_score
                    
                    # Research scores tab
                    with scoring_tabs[1]:
                        st.markdown("### Research-Oriented Scores")
                        updated_research_scores = {}
                        
                        for key, score in research_scores.items():
                            description = framework_criteria.get('research', {}).get(key, key)
                            updated_score = st.slider(
                                f"{description} ({key})",
                                min_value=0.0,
                                max_value=3.0,
                                value=float(score),
                                step=0.1,
                                key=f"edit_score_research_{key}"
                            )
                            updated_research_scores[key] = updated_score
                    
                    # Intelligence scores tab
                    with scoring_tabs[2]:
                        st.markdown("### Intelligence-Oriented Scores")
                        updated_intelligence_scores = {}
                        
                        for key, score in intelligence_scores.items():
                            description = framework_criteria.get('intelligence', {}).get(key, key)
                            updated_score = st.slider(
                                f"{description} ({key})",
                                min_value=0.0,
                                max_value=3.0,
                                value=float(score),
                                step=0.1,
                                key=f"edit_score_intelligence_{key}"
                            )
                            updated_intelligence_scores[key] = updated_score
                    
                    # Resource scores tab
                    with scoring_tabs[3]:
                        st.markdown("### Resource-Oriented Scores")
                        updated_resource_scores = {}
                        
                        for key, score in resource_scores.items():
                            description = framework_criteria.get('resource', {}).get(key, key)
                            updated_score = st.slider(
                                f"{description} ({key})",
                                min_value=0.0,
                                max_value=3.0,
                                value=float(score),
                                step=0.1,
                                key=f"edit_score_resource_{key}"
                            )
                            updated_resource_scores[key] = updated_score
                    
                    # Additional scores tab
                    with scoring_tabs[4]:
                        st.markdown("### Additional Criteria Scores")
                        updated_additional_scores = {}
                        
                        for key, score in additional_scores.items():
                            data = framework_additional.get(key, {})
                            description = data.get('description', key)
                            weight = additional_weights.get(key, 0.5)
                            score_type = data.get('type', 'positive')
                            
                            # Calculate the score range based on the criteria type
                            if score_type == 'positive':
                                min_val, max_val = 0.0, 1.0
                            elif score_type == 'negative':
                                min_val, max_val = -1.0, 0.0
                            else:  # bidirectional
                                min_val, max_val = -1.0, 1.0
                            
                            updated_score = st.slider(
                                f"{description} ({key}, type: {score_type}, weight: {weight})",
                                min_value=min_val,
                                max_value=max_val,
                                value=float(score),
                                step=0.1,
                                key=f"edit_score_additional_{key}"
                            )
                            updated_additional_scores[key] = updated_score
                    
                    # Calculate updated scores
                    scores = calculate_scores(
                        updated_service_scores,
                        updated_research_scores,
                        updated_intelligence_scores,
                        updated_resource_scores,
                        updated_additional_scores,
                        additional_weights
                    )
                    
                    # Display calculated scores
                    st.markdown("### Calculated Scores")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Service-Research Score", f"{scores.get('service_research_score', (0,0))}")
                    with col2:
                        st.metric("Intelligence-Resource Score", f"{scores.get('intelligence_resource_score', (0,0))}")
                    with col3:
                        st.metric("Total Score", f"{scores.get('total_score', 0):.2f}")
                        st.metric("Tier", scores.get('tier', 'N/A'))
                    
                    # Save button for updated compass
                    if st.button("Save Compass Changes", key="save_compass_changes"):
                        # Update the compass data
                        updated_compass = selected_compass.copy()
                        updated_compass["name"] = compass_name
                        updated_compass["uid"] = compass_uid
                        updated_compass["description"] = compass_description
                        updated_compass["updated_at"] = datetime.now().isoformat()
                        updated_compass["service_oriented_scores"] = updated_service_scores
                        updated_compass["research_oriented_scores"] = updated_research_scores
                        updated_compass["intelligence_oriented_scores"] = updated_intelligence_scores
                        updated_compass["resource_oriented_scores"] = updated_resource_scores
                        updated_compass["additional_criteria_scores"] = {
                            "scores": updated_additional_scores,
                            "weights": additional_weights
                        }
                        updated_compass["service_research_score"] = scores.get('service_research_score', (0,0))
                        updated_compass["intelligence_resource_score"] = scores.get('intelligence_resource_score', (0,0))
                        updated_compass["total_score"] = scores.get('total_score', 0)
                        updated_compass["tier"] = scores.get('tier', 'N/A')
                        
                        # Save the updated compass
                        filepath = selected_compass.get('_filepath', '')
                        success, result = save_compass(updated_compass, filepath)
                        
                        if success:
                            st.success(f"Compass evaluation '{compass_name}' updated successfully!")
                            # Force a reload
                            st.rerun()
                        else:
                            st.error(f"Error updating compass evaluation: {result}")
        
        elif compass_section == "Export Compass Evaluation":
            st.markdown("## Export Compass Evaluation")
            
            if not all_compasses:
                st.warning("No compass evaluations available to export.")
            else:
                # Select a compass to export
                export_compass_name = st.selectbox("Select Compass to Export", compass_names, key="export_compass")
                
                # Find the selected compass
                export_compass = next((c for c in all_compasses if c['name'] == export_compass_name), None)
                
                if export_compass and st.button("Prepare for Export", key="prepare_compass_export"):
                    # Remove internal filepath before exporting
                    export_data = export_compass.copy()
                    if '_filepath' in export_data:
                        del export_data['_filepath']
                    
                    # Convert to JSON
                    compass_json = json.dumps(export_data, indent=4)
                    
                    # Create a download button for the JSON file
                    st.download_button(
                        label="Download Compass JSON",
                        data=compass_json,
                        file_name=f"{export_compass_name.lower().replace(' ', '_')}_compass.json",
                        mime="application/json"
                    )
                    
                    st.success(f"Compass evaluation '{export_compass_name}' ready for download.")
        
        elif compass_section == "Delete Compass Evaluation":
            st.markdown("## Delete Compass Evaluation")
            
            if not all_compasses:
                st.warning("No compass evaluations available to delete.")
            else:
                # Select a compass to delete
                delete_compass_name = st.selectbox("Select Compass to Delete", compass_names, key="delete_compass")
                
                # Find the selected compass
                delete_compass = next((c for c in all_compasses if c['name'] == delete_compass_name), None)
                
                if delete_compass:
                    st.warning(f"Are you sure you want to delete the compass evaluation '{delete_compass_name}'? This action cannot be undone.")
                    
                    # Confirm deletion
                    if st.button("Confirm Deletion", key="confirm_compass_delete"):
                        if '_filepath' in delete_compass:
                            # Delete the compass file
                            success = delete_compass(delete_compass['_filepath'])
                            
                            if success:
                                st.success(f"Compass evaluation '{delete_compass_name}' deleted successfully!")
                                # Force a reload
                                st.rerun()
                            else:
                                st.error(f"Error deleting compass evaluation.")
                        else:
                            st.error(f"Compass file path not found.")
    
    # Back button
    if st.button("Return to Main App", key="return_btn"):
        st.query_params.clear()
        st.rerun()

def show_login_page():
    """Show the login page for the admin console."""
    st.markdown('<h1 class="main-header">Sherpa Admin Login</h1>', unsafe_allow_html=True)
    
    # Add custom CSS for login form
    st.markdown("""
    <style>
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #f8f9fa;
        border-radius: 10px;
    }
    .login-header {
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
        color: #333;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Login form
    with st.form("login_form"):
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="login-header">Login to Admin Console</h2>', unsafe_allow_html=True)
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        # Hard-coded credentials (in a real app, use secure authentication)
        ADMIN_USERNAME = "admin"
        ADMIN_PASSWORD = "sherpa2024"
        
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state["admin_authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Add a button to return to the main app
    if st.button("Return to Main App", key="login_return_btn"):
        st.query_params.clear()
        st.rerun()

def navigation():
    """Create the sidebar navigation menu."""
    # Check for admin access via query parameter (maintaining both 'admin' and 'xerpa' for compatibility)
    params = st.query_params
    if params.get("page") in ["xerpa", "admin"]:
        # Show admin console - password protected
        admin_console_page()
        return
        
    with st.sidebar:
        # Show Sherpa logo at the top
        logo_path = "assets/sherpa_logo.png"
        
        if os.path.exists(logo_path):
            st.image(logo_path, use_column_width=True)
        else:
            st.title("Sherpa")
            
        st.markdown("---")  # Separator
        
        # Navigation menu
        st.markdown("<h3>Navigation</h3>", unsafe_allow_html=True)
        
        # Navigation links - define available pages (simplified for user portal)
        pages = {
            "Home": home_page,
            "Visualization": visualization_page
        }
        
        # Check if there are any subnets
        subnets_df = get_subnets()
        has_subnets = not subnets_df.empty
        
        # Navigation control with buttons
        # Get current page
        current_page = st.session_state.get('page', 'Home')
        
        for page_name, page_func in pages.items():
            # Disable buttons if no subnets available
            disabled = False
            if not has_subnets and page_name in ["Visualization"]:
                disabled = True
            
            # Determine if this is the active button
            is_active = current_page == page_name
            
            # Generate class for active button
            button_type = "primary" if is_active else "secondary"
            
            # Show button with appropriate style
            if st.button(page_name, disabled=disabled, key=f"nav_{page_name}", 
                        use_container_width=True, type=button_type):
                st.session_state['page'] = page_name
                st.rerun()
            
        st.markdown("---")  # Final separator

        # Add logging information in the sidebar
        st.markdown("<h3>Debug Info</h3>", unsafe_allow_html=True)
        st.markdown(f"Current page: **{current_page}**")
        st.markdown(f"Subnets available: **{'Yes' if has_subnets else 'No'}**")
        
        # Add version information
        st.markdown("---")
        st.markdown("<div style='font-size: 0.8em; color: #888;'>Sherpa v1.0.0</div>", unsafe_allow_html=True)
        
        # Get current page selection
        selection = st.session_state.get('page', 'Home')
        
        # Disable certain pages if no subnets exist
        if not has_subnets and selection in ["Visualization"]:
            selection = "Home"
    
    # Call the selected page function
    if selection in pages:
        pages[selection]()
    else:
        # Default to home page if selection not valid
        home_page()

def home_page():
    """Display the home page."""
    st.markdown('<h1 class="main-header">Sherpa</h1>', unsafe_allow_html=True)
    
    # Add custom CSS to increase font size for the home page
    st.markdown("""
    <style>
    /* Increase font size for all text in the home page by 25% */
    .home-text {
        font-size: 1.25rem;
    }
    .home-text h2 {
        font-size: 1.75rem;
    }
    .home-text li {
        font-size: 1.25rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Columna única para el contenido de introducción
    st.markdown("""
    <div class="home-text">
    Welcome to Sherpa, a tool designed to analyze and visualize Bittensor subnets 
    based on their characteristics and performance metrics.
    
    This platform helps you:
    <ul>
    <li>Categorize subnets on a Service-Research and Intelligence-Resource spectrum</li>
    <li>Score subnets based on multiple weighted criteria</li>
    <li>Visualize subnet positioning and relationships</li>
    <li>Compare subnet performance and capabilities</li>
    </ul>
    
    <h2>Key Concepts</h2>
    
    <p>Sherpa works with two main components:</p>
    
    <ul>
    <li><strong>Frameworks</strong> - These are the evaluation templates that define what criteria to use when assessing subnets. A framework contains the definitions of all criteria across four main categories (Service, Research, Intelligence, Resource) and additional weighted criteria.</li>
    <li><strong>Compass Evaluations</strong> - These are specific subnet assessments made using a framework. A compass evaluation applies a framework's criteria to a specific subnet and captures the scoring.</li>
    </ul>
    
    <p>This separation allows you to:</p>
    <ul>
    <li>Evaluate many subnets using the same framework for consistency</li>
    <li>Compare evaluations across frameworks</li>
    <li><del>Create multiple frameworks with different criteria for different purposes</del> <span style="background-color: #e7f3fe; padding: 2px 5px; border-radius: 3px; font-size: 0.8em;">V2</span></li>
    </ul>
    
    <h2>Getting Started</h2>
    
    <ol>
    <li><strong>Select a Framework</strong> - Choose or create an evaluation framework for your analysis.</li>
    <li><strong>Create a Compass Evaluation</strong> - Apply the framework to evaluate specific subnets.</li>
    <li><strong>Visualization</strong> - Explore interactive visualizations of your subnet evaluations.</li>
    </ol>
    
    Use the navigation menu on the left to begin.
    </div>
    """, unsafe_allow_html=True)

    # Crear dos columnas con proporción 7:5 para posicionar la imagen y el botón a la izquierda
    journey_col1, journey_col2 = st.columns([7, 5])
    
    with journey_col1:
        # Custom CSS para la imagen y el botón - reducido en anchura y pegado
        st.markdown("""
        <style>
        .journey-container {
            max-width: 70%; /* Reducido en 15% del 85% anterior */
            margin-left: 0; /* Alinear a la izquierda */
        }
        .larger-image img {
            width: 100%;
            margin-bottom: -10px; /* Eliminar espacio entre imagen y botón */
        }
        .journey-button button {
            width: 100%;
            margin-top: -1px; /* Espacio negativo para pegar el botón a la imagen */
            border-top-left-radius: 0; /* Elimina el redondeado superior del botón */
            border-top-right-radius: 0; /* Elimina el redondeado superior del botón */
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Contenedor para la imagen y el botón juntos
        st.markdown('<div class="journey-container">', unsafe_allow_html=True)
        
        # Display the mountain journey image con borde inferior eliminado
        mountains_path = "assets/journey_mountains.png"
        if os.path.exists(mountains_path):
            st.markdown('<div class="larger-image" style="border-bottom: none;">', unsafe_allow_html=True)
            st.image(mountains_path, use_column_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # "Start Journey" button con estilo primario pegado a la imagen
        st.markdown('<div class="journey-button">', unsafe_allow_html=True)
        if st.button("Explore Subnets", type="primary", key="start_journey_btn", use_container_width=True):
            # Set the page to the visualization page
            print("LOG: User clicked 'Explore Subnets' button")
            st.session_state['page'] = "Visualization"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Cerrar el contenedor
        st.markdown('</div>', unsafe_allow_html=True)
    
    # La columna journey_col2 queda vacía intencionalmente para dar espacio
    
    # Roadmap section
    st.markdown('<h2 class="section-header" style="margin-bottom: 0px;">Development Roadmap</h2>', unsafe_allow_html=True)
    
    # Create container for the roadmap using native Streamlit components (sin espacio extra)
    with st.container():
        # Add light gray background and padding
        st.markdown('<div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">', unsafe_allow_html=True)
        
        # Create three columns for the versions
        col1, col2, col3 = st.columns(3)
        
        # CSS to disable interactions with images
        st.markdown("""
        <style>
        .no-interact img {
            pointer-events: none !important;
        }
        .roadmap-text {
            font-size: 1.25rem;
        }
        .roadmap-title {
            font-size: 1.5rem;
            font-weight: bold;
        }
        .roadmap-subtitle {
            font-size: 1.25rem;
            margin-top: 10px;
        }
        .roadmap-description {
            font-size: 1.15rem;
            margin-top: 5px;
        }
        .roadmap-info {
            font-size: 1.15rem;
            text-align: center;
            margin-top: 10px;
            font-style: italic;
            color: #666;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Version 1 (Current)
        with col1:
            st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
            st.markdown('<div style="background-color: #4d68e9; color: white; width: 60px; height: 60px; border-radius: 30px; margin: 0 auto; display: flex; justify-content: center; align-items: center; font-weight: bold; font-size: 1.25rem;">V1</div>', unsafe_allow_html=True)
            st.markdown('<div class="roadmap-subtitle" style="font-weight: bold; color: #4d68e9;">Current Version</div>', unsafe_allow_html=True)
            st.markdown('<div class="roadmap-description">Subnet evaluation framework</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Version 2 (Coming Soon)
        with col2:
            st.markdown('<div class="no-interact" style="text-align: center;">', unsafe_allow_html=True)
            # Use image instead of circle with V2 text, with interaction disabled
            st.image("assets/sherpa_v2_logo.png", width=130, use_column_width=False)  
            st.markdown('<div class="roadmap-subtitle" style="font-weight: bold; color: #888;">Coming Soon</div>', unsafe_allow_html=True)
            st.markdown('<div class="roadmap-description">More Sherpas</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Version 3 (Future)
        with col3:
            st.markdown('<div class="no-interact" style="text-align: center;">', unsafe_allow_html=True)
            # Use footprint image instead of circle with V3 text, with interaction disabled
            st.image("assets/sherpa_v3_logo.png", width=130, use_column_width=False)
            st.markdown('<div class="roadmap-subtitle" style="font-weight: bold; color: #888;">Future</div>', unsafe_allow_html=True)
            st.markdown('<div class="roadmap-description">Follow the Sherpa</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Progress bar
        st.progress(0.20)  # Indicates we're at 20% of the roadmap (v1 of 3)
        
        # Informational text at the bottom
        st.markdown('<div class="roadmap-info">We\'re constantly improving Sherpa to provide better subnet evaluation tools for the Bittensor ecosystem.</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def framework_selection_page():
    """Page for selecting a framework. (DEPRECATED - TO BE REMOVED)"""
    # This page is deprecated and should be removed in future versions.
    # All framework selection now happens in the admin panel
    st.markdown('<h1 class="main-header">Select Evaluation Framework</h1>', unsafe_allow_html=True)
    
    # Add custom CSS to increase font size
    st.markdown("""
    <style>
    /* Increase font size for framework selection page by 25% */
    .framework-text {
        font-size: 1.25rem;
    }
    .framework-text ul li {
        font-size: 1.25rem;
        margin-bottom: 0.5rem;
    }
    .framework-badge {
        display: inline-block; 
        background-color: #28a745; 
        color: white; 
        padding: 0.3rem 0.6rem; 
        border-radius: 0.25rem; 
        font-size: 1.1rem; 
        font-weight: 600; 
        margin-bottom: 1rem;
    }
    /* Tooltip container */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    /* Tooltip text */
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 250px;
        background-color: #555;
        color: #fff;
        text-align: left;
        border-radius: 6px;
        padding: 10px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -125px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    /* Tooltip arrow */
    .tooltip .tooltiptext::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: #555 transparent transparent transparent;
    }
    
    /* Show tooltip on hover */
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Load only active frameworks from JSON files (for user view)
    frameworks = load_frameworks(only_active=True)
    
    if not frameworks:
        st.warning("No frameworks found. Please use the Admin Console to create a framework first.")
        
        # For backwards compatibility, still provide the default framework
        st.markdown("### Using Default Sherpa Framework")
        available_frameworks = ["Sherpa Framework"]
        selected_framework = "Sherpa Framework"
        framework_data = {
            "name": "Sherpa Framework",
            "description": "Standard framework for subnet classification",
            "criteria": {
                "service": get_evaluation_criteria()['service'],
                "research": get_evaluation_criteria()['research'],
                "intelligence": get_evaluation_criteria()['intelligence'],
                "resource": get_evaluation_criteria()['resource'],
            },
            "additional_criteria": get_additional_evaluation_criteria()
        }
    else:
        # Get framework names for the dropdown
        available_frameworks = [f["name"] for f in frameworks]
        
        # Framework selection dropdown
        selected_framework = st.selectbox(
            "Choose a framework:",
            available_frameworks
        )
        
        # Get the selected framework data
        framework_data = next((f for f in frameworks if f["name"] == selected_framework), None)
        
        # Add recommended badge if it's the default framework
        if selected_framework == "Sherpa Default Framework":
            st.markdown('<span class="framework-badge">✓ Recommended</span>', unsafe_allow_html=True)
    
    # Main framework details section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<h2 class="section-header">Framework Description</h2>', unsafe_allow_html=True)
        
        if framework_data:
            framework_description = framework_data.get("description", "")
            
            st.markdown(f"""
            <div class="framework-text">
            {framework_description}
            
            <ul>
            <li><strong>Service vs. Research Orientation</strong>: Measures whether a subnet focuses more on providing practical services or advancing research.</li>
            <li><strong>Intelligence vs. Resource Provision</strong>: Evaluates whether a subnet primarily offers intelligent processing or computational resources.</li>
            </ul>
            
            Additionally, the framework includes supplementary criteria for a more comprehensive evaluation.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="framework-text">
            This framework provides a standardized approach to analyzing and categorizing Bittensor subnets
            along two primary axes:
            
            <ul>
            <li><strong>Service vs. Research Orientation</strong>: Measures whether a subnet focuses more on providing practical services or advancing research.</li>
            <li><strong>Intelligence vs. Resource Provision</strong>: Evaluates whether a subnet primarily offers intelligent processing or computational resources.</li>
            </ul>
            
            Additionally, the framework includes supplementary criteria for a more comprehensive evaluation.
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<h3 class="subsection-header">Framework Stats</h3>', unsafe_allow_html=True)
        
        # Get subnet count from the database
        subnets_df = get_subnets()
        subnet_count = len(subnets_df) if not subnets_df.empty else 0
        
        # Load compasses that use this framework
        compasses = load_compasses()
        framework_compasses = [c for c in compasses if c.get('framework') == selected_framework]
        compass_count = len(framework_compasses)
        
        # Count criteria
        if framework_data:
            criteria_count = 0
            for category in framework_data.get('criteria', {}).values():
                criteria_count += len(category)
            
            additional_count = len(framework_data.get('additional_criteria', {}))
            
            # Display metrics
            st.metric("Main Criteria", str(criteria_count))
            st.metric("Additional Criteria", str(additional_count))
            st.metric("Dimensions", "4")
            st.metric("Compass Evaluations", str(compass_count))
        else:
            # Default values if framework data not available
            st.metric("Evaluation Criteria", "26")
            st.metric("Dimensions", "4")
            st.metric("Subnets in Framework", subnet_count)
        
        # Espacio en blanco para mantener el espaciado entre secciones
        st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
    
    # Show framework criteria details if a framework is selected
    if framework_data:
        with st.expander("View Framework Criteria"):
            criteria_tabs = st.tabs(["Service Criteria", "Research Criteria", "Intelligence Criteria", "Resource Criteria", "Additional Criteria"])
            
            # Service criteria
            with criteria_tabs[0]:
                st.markdown("### Service-Oriented Criteria")
                service_criteria = framework_data.get('criteria', {}).get('service', {})
                for key, data in service_criteria.items():
                    # Handle both old format (string) and new format (dict with question and description)
                    if isinstance(data, dict):
                        question = data.get('question', '')
                        description = data.get('description', '')
                        if description:
                            # Mostrar pregunta con botón de información que muestra descripción al hacer hover
                            st.markdown(f"""
                            <div>
                                <span style="font-weight: bold;">{key}</span>: {question} 
                                <span class="tooltip">
                                    <span style="display: inline-block; border-radius: 50%; background-color: #6c757d; color: white; width: 18px; height: 18px; text-align: center; font-size: 12px; margin-left: 5px; cursor: help;">i</span>
                                    <span class="tooltiptext">{description}</span>
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"**{key}**: {question}")
                    else:
                        # Backward compatibility for old format
                        st.markdown(f"**{key}**: {data}")
            
            # Research criteria
            with criteria_tabs[1]:
                st.markdown("### Research-Oriented Criteria")
                research_criteria = framework_data.get('criteria', {}).get('research', {})
                for key, data in research_criteria.items():
                    # Handle both old format (string) and new format (dict with question and description)
                    if isinstance(data, dict):
                        question = data.get('question', '')
                        description = data.get('description', '')
                        if description:
                            # Mostrar pregunta con botón de información que muestra descripción al hacer hover
                            st.markdown(f"""
                            <div>
                                <span style="font-weight: bold;">{key}</span>: {question} 
                                <span class="tooltip">
                                    <span style="display: inline-block; border-radius: 50%; background-color: #6c757d; color: white; width: 18px; height: 18px; text-align: center; font-size: 12px; margin-left: 5px; cursor: help;">i</span>
                                    <span class="tooltiptext">{description}</span>
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"**{key}**: {question}")
                    else:
                        # Backward compatibility for old format
                        st.markdown(f"**{key}**: {data}")
            
            # Intelligence criteria
            with criteria_tabs[2]:
                st.markdown("### Intelligence-Oriented Criteria")
                intelligence_criteria = framework_data.get('criteria', {}).get('intelligence', {})
                for key, data in intelligence_criteria.items():
                    # Handle both old format (string) and new format (dict with question and description)
                    if isinstance(data, dict):
                        question = data.get('question', '')
                        description = data.get('description', '')
                        if description:
                            # Mostrar pregunta con botón de información que muestra descripción al hacer hover
                            st.markdown(f"""
                            <div>
                                <span style="font-weight: bold;">{key}</span>: {question} 
                                <span class="tooltip">
                                    <span style="display: inline-block; border-radius: 50%; background-color: #6c757d; color: white; width: 18px; height: 18px; text-align: center; font-size: 12px; margin-left: 5px; cursor: help;">i</span>
                                    <span class="tooltiptext">{description}</span>
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"**{key}**: {question}")
                    else:
                        # Backward compatibility for old format
                        st.markdown(f"**{key}**: {data}")
            
            # Resource criteria
            with criteria_tabs[3]:
                st.markdown("### Resource-Oriented Criteria")
                resource_criteria = framework_data.get('criteria', {}).get('resource', {})
                for key, data in resource_criteria.items():
                    # Handle both old format (string) and new format (dict with question and description)
                    if isinstance(data, dict):
                        question = data.get('question', '')
                        description = data.get('description', '')
                        if description:
                            # Mostrar pregunta con botón de información que muestra descripción al hacer hover
                            st.markdown(f"""
                            <div>
                                <span style="font-weight: bold;">{key}</span>: {question} 
                                <span class="tooltip">
                                    <span style="display: inline-block; border-radius: 50%; background-color: #6c757d; color: white; width: 18px; height: 18px; text-align: center; font-size: 12px; margin-left: 5px; cursor: help;">i</span>
                                    <span class="tooltiptext">{description}</span>
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"**{key}**: {question}")
                    else:
                        # Backward compatibility for old format
                        st.markdown(f"**{key}**: {data}")
            
            # Additional criteria
            with criteria_tabs[4]:
                st.markdown("### Additional Criteria")
                additional_criteria = framework_data.get('additional_criteria', {})
                for key, data in additional_criteria.items():
                    weight = data.get('weight', 0.5)
                    crit_type = data.get('type', 'positive')
                    question = data.get('question', '')
                    description = data.get('description', '')
                    
                    # Mostrar con formato y tooltip si hay descripción detallada
                    if description:
                        st.markdown(f"""
                        <div>
                            <span style="font-weight: bold;">{key}</span> (weight: {weight}, type: {crit_type}): {question}
                            <span class="tooltip">
                                <span style="display: inline-block; border-radius: 50%; background-color: #6c757d; color: white; width: 18px; height: 18px; text-align: center; font-size: 12px; margin-left: 5px; cursor: help;">i</span>
                                <span class="tooltiptext">{description}</span>
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{key}** (weight: {weight}, type: {crit_type}): {question}")
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Create New Evaluation", type="primary", key="create_eval_btn", use_container_width=True):
            # Store selected framework in session
            st.session_state['selected_framework'] = selected_framework
            # Navigate to add subnets page
            print(f"LOG: Redirecting to Add Subnets page for framework: {selected_framework}")
            # Launch the add_subnets_page function directly
            add_subnets_page()
            return
    
    with col2:
        if compass_count > 0:
            if st.button("View Existing Evaluations", type="secondary", key="view_eval_btn", use_container_width=True):
                # Navigate to visualization page
                print(f"LOG: Redirecting to Visualization page for framework: {selected_framework}")
                st.session_state['page'] = "2. Visualization"
                st.rerun()
    
    with col3:
        # Espacio vacío para mantener la estructura de columnas
        st.markdown("&nbsp;", unsafe_allow_html=True)

def modify_framework_page():
    """Page for modifying the evaluation framework."""
    st.markdown('<h1 class="main-header">Modify Framework</h1>', unsafe_allow_html=True)
    
    # Get evaluation criteria
    main_criteria = get_evaluation_criteria()
    additional_criteria = get_additional_evaluation_criteria()
    
    # Check if the form was submitted
    if 'framework_submitted' not in st.session_state:
        st.session_state.framework_submitted = False
    
    # Create form for adjusting criteria
    with st.form("framework_form"):
        st.markdown('<h2 class="section-header">1. Determine the subnet\'s nature</h2>', unsafe_allow_html=True)
        
        # Display criteria in a 2x2 grid
        col1, col2 = st.columns(2)
        
        # Service-Oriented Criteria (top left)
        with col1:
            st.markdown('<div class="criteria-section">', unsafe_allow_html=True)
            st.markdown('<h3 class="subsection-header" style="color: #28a745;">Service-Oriented Criteria</h3>', unsafe_allow_html=True)
            
            service_scores = {}
            for key, description in main_criteria['service'].items():
                st.markdown(f"##### {description}")
                service_scores[key] = st.slider(
                    "Score", 
                    min_value=0.0, 
                    max_value=10.0, 
                    value=5.0, 
                    step=0.1,
                    key=f"service_{key}",
                    label_visibility="collapsed"
                )
                st.markdown(f'<div class="fine-adjust">Value: <b>{service_scores[key]}</b></div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Research-Oriented Criteria (top right)
        with col2:
            st.markdown('<div class="criteria-section">', unsafe_allow_html=True)
            st.markdown('<h3 class="subsection-header" style="color: #17a2b8;">Research-Oriented Criteria</h3>', unsafe_allow_html=True)
            
            research_scores = {}
            for key, description in main_criteria['research'].items():
                st.markdown(f"##### {description}")
                research_scores[key] = st.slider(
                    "Score", 
                    min_value=0.0, 
                    max_value=10.0, 
                    value=5.0, 
                    step=0.1,
                    key=f"research_{key}",
                    label_visibility="collapsed"
                )
                st.markdown(f'<div class="fine-adjust">Value: <b>{research_scores[key]}</b></div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        col3, col4 = st.columns(2)
        
        # Intelligence-Oriented Criteria (bottom left)
        with col3:
            st.markdown('<div class="criteria-section">', unsafe_allow_html=True)
            st.markdown('<h3 class="subsection-header" style="color: #ffc107;">Intelligence-Oriented Criteria</h3>', unsafe_allow_html=True)
            
            intelligence_scores = {}
            for key, description in main_criteria['intelligence'].items():
                st.markdown(f"##### {description}")
                intelligence_scores[key] = st.slider(
                    "Score", 
                    min_value=0.0, 
                    max_value=10.0, 
                    value=5.0, 
                    step=0.1,
                    key=f"intelligence_{key}",
                    label_visibility="collapsed"
                )
                st.markdown(f'<div class="fine-adjust">Value: <b>{intelligence_scores[key]}</b></div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Resource-Oriented Criteria (bottom right)
        with col4:
            st.markdown('<div class="criteria-section">', unsafe_allow_html=True)
            st.markdown('<h3 class="subsection-header" style="color: #dc3545;">Resource-Oriented Criteria</h3>', unsafe_allow_html=True)
            
            resource_scores = {}
            for key, description in main_criteria['resource'].items():
                st.markdown(f"##### {description}")
                resource_scores[key] = st.slider(
                    "Score", 
                    min_value=0.0, 
                    max_value=10.0, 
                    value=5.0, 
                    step=0.1,
                    key=f"resource_{key}",
                    label_visibility="collapsed"
                )
                st.markdown(f'<div class="fine-adjust">Value: <b>{resource_scores[key]}</b></div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Additional criteria section
        st.markdown('<h2 class="section-header">2. Additional Evaluation Criteria</h2>', unsafe_allow_html=True)
        
        st.markdown('<div class="criteria-section">', unsafe_allow_html=True)
        
        # Create columns for additional criteria
        additional_scores = {}
        custom_weights = {}
        
        for i, (key, data) in enumerate(additional_criteria.items()):
            # Create a new row for every 2 criteria
            if i % 2 == 0:
                cols = st.columns(2)
            
            # Create columns for label and controls
            with cols[i % 2]:
                # Format the badge for criteria type
                badge_class = ""
                if data["type"] == "positive":
                    badge_class = "badge-positive"
                elif data["type"] == "negative":
                    badge_class = "badge-negative"
                else:  # bidirectional
                    badge_class = "badge-bidirectional"
                
                # Display criteria with badge
                st.markdown(f'<div><span>{data["description"]}</span> <span class="badge {badge_class}">{data["type"]}</span></div>', unsafe_allow_html=True)
                
                # Create two columns for slider and weight
                score_col, weight_col = st.columns([3, 1])
                
                with score_col:
                    # Create slider for score
                    additional_scores[key] = st.slider(
                        "Score",
                        min_value=0.0,
                        max_value=10.0,
                        value=5.0,
                        step=0.1,
                        key=f"additional_{key}",
                        label_visibility="collapsed"
                    )
                
                with weight_col:
                    # Create number input for weight
                    custom_weights[key] = {
                        "weight": st.number_input(
                            "Weight",
                            min_value=0.1,
                            max_value=3.0,
                            value=data["weight"],
                            step=0.1,
                            key=f"weight_{key}",
                            label_visibility="collapsed"
                        ),
                        "type": data["type"]
                    }
                
                # Show current values
                st.markdown(f'<div class="fine-adjust">Value: <b>{additional_scores[key]}</b> | Weight: <b>{custom_weights[key]["weight"]}</b></div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Submit button
        submitted = st.form_submit_button("Save Framework Changes", type="primary")
        
        if submitted:
            # Create framework data
            framework_data = {
                "name": "Framework Settings",
                "uid": "framework_settings",
                "description": "Modified framework settings and weights",
                "service_oriented_scores": service_scores,
                "research_oriented_scores": research_scores,
                "intelligence_oriented_scores": intelligence_scores,
                "resource_oriented_scores": resource_scores,
                "additional_criteria_scores": {
                    "scores": additional_scores,
                    "weights": custom_weights
                }
            }
            
            # Save to database
            save_subnet(framework_data)
            
            st.session_state.framework_submitted = True
            st.rerun()
    
    # Show success message if the form was submitted
    if st.session_state.framework_submitted:
        st.success("Framework settings saved successfully!")
        
        # Reset the flag
        st.session_state.framework_submitted = False
        
        # Redirect to add subnets page
        st.markdown("""
        <script>
        setTimeout(function() {
            window.location.href = '/?page=add_subnets';
        }, 2000);
        </script>
        """, unsafe_allow_html=True)

def add_subnets_page():
    """Page for adding subnet data (now creates Compass evaluations)."""
    st.markdown('<h1 class="main-header">Create New Compass Evaluation</h1>', unsafe_allow_html=True)
    
    # Get selected framework from session state or use default
    framework_name = st.session_state.get('selected_framework', 'Sherpa Default Framework')
    
    # Load available frameworks
    frameworks = load_frameworks()
    
    if not frameworks:
        st.warning("""No frameworks found. Please go to Admin Console to create a framework first.
                    Using default evaluation criteria for now.""")
        # Use default criteria
        main_criteria = get_evaluation_criteria()
        additional_criteria = get_additional_evaluation_criteria()
        framework_data = {
            "name": "Sherpa Default Framework",
            "description": "Default framework for subnet classification",
        }
    else:
        # Allow the user to select a framework if not already selected
        if 'selected_framework' not in st.session_state:
            available_frameworks = [f["name"] for f in frameworks]
            framework_name = st.selectbox("Select Framework for Evaluation:", available_frameworks)
        
        # Find the selected framework data
        framework_data = next((f for f in frameworks if f['name'] == framework_name), None)
        
        if not framework_data:
            st.error(f"Framework '{framework_name}' not found. Using default criteria.")
            main_criteria = get_evaluation_criteria()
            additional_criteria = get_additional_evaluation_criteria()
        else:
            # Get criteria from the framework
            main_criteria = framework_data.get('criteria', {})
            additional_criteria = framework_data.get('additional_criteria', {})
    
    # Display the selected framework
    st.info(f"Creating evaluation using framework: **{framework_name}**")
    
    # Get existing subnets
    subnets_df = get_subnets()
    has_subnets = not subnets_df.empty
    
    # Initialize session state for subnet editing
    if 'editing_subnet' not in st.session_state:
        st.session_state.editing_subnet = False
        st.session_state.subnet_to_edit = None
    
    # Add or Edit Subnet Form
    with st.form("subnet_form"):
        if st.session_state.editing_subnet:
            st.markdown('<h2 class="section-header">Edit Subnet</h2>', unsafe_allow_html=True)
            subnet_data = st.session_state.subnet_to_edit
        else:
            st.markdown('<h2 class="section-header">Add New Subnet</h2>', unsafe_allow_html=True)
            subnet_data = None
        
        # Basic Information
        col1, col2 = st.columns(2)
        
        with col1:
            subnet_name = st.text_input("Subnet Name", value=subnet_data['name'] if subnet_data else "")
            subnet_uid = st.text_input("Subnet UID", value=subnet_data['uid'] if subnet_data else "")
        
        with col2:
            subnet_description = st.text_area("Description", value=subnet_data['description'] if subnet_data else "", height=82)
        
        st.markdown('<h3 class="subsection-header">Evaluation Criteria</h3>', unsafe_allow_html=True)
        
        # Create tabs for different criteria categories
        tabs = st.tabs(["Service", "Research", "Intelligence", "Resource", "Additional"])
        
        # Service-oriented criteria
        with tabs[0]:
            service_scores = {}
            if subnet_data and 'service_oriented_scores' in subnet_data:
                default_scores = subnet_data['service_oriented_scores']
            else:
                default_scores = {}
            
            for key, description in main_criteria['service'].items():
                default_value = default_scores.get(key, 5.0)
                service_scores[key] = st.slider(
                    description,
                    min_value=0.0,
                    max_value=10.0,
                    value=default_value,
                    step=0.1,
                    key=f"subnet_service_{key}"
                )
        
        # Research-oriented criteria
        with tabs[1]:
            research_scores = {}
            if subnet_data and 'research_oriented_scores' in subnet_data:
                default_scores = subnet_data['research_oriented_scores']
            else:
                default_scores = {}
            
            for key, description in main_criteria['research'].items():
                default_value = default_scores.get(key, 5.0)
                research_scores[key] = st.slider(
                    description,
                    min_value=0.0,
                    max_value=10.0,
                    value=default_value,
                    step=0.1,
                    key=f"subnet_research_{key}"
                )
        
        # Intelligence-oriented criteria
        with tabs[2]:
            intelligence_scores = {}
            if subnet_data and 'intelligence_oriented_scores' in subnet_data:
                default_scores = subnet_data['intelligence_oriented_scores']
            else:
                default_scores = {}
            
            for key, description in main_criteria['intelligence'].items():
                default_value = default_scores.get(key, 5.0)
                intelligence_scores[key] = st.slider(
                    description,
                    min_value=0.0,
                    max_value=10.0,
                    value=default_value,
                    step=0.1,
                    key=f"subnet_intelligence_{key}"
                )
        
        # Resource-oriented criteria
        with tabs[3]:
            resource_scores = {}
            if subnet_data and 'resource_oriented_scores' in subnet_data:
                default_scores = subnet_data['resource_oriented_scores']
            else:
                default_scores = {}
            
            for key, description in main_criteria['resource'].items():
                default_value = default_scores.get(key, 5.0)
                resource_scores[key] = st.slider(
                    description,
                    min_value=0.0,
                    max_value=10.0,
                    value=default_value,
                    step=0.1,
                    key=f"subnet_resource_{key}"
                )
        
        # Additional criteria
        with tabs[4]:
            additional_scores = {}
            if subnet_data and 'additional_criteria_scores' in subnet_data:
                if isinstance(subnet_data['additional_criteria_scores'], dict) and 'scores' in subnet_data['additional_criteria_scores']:
                    default_scores = subnet_data['additional_criteria_scores']['scores']
                else:
                    default_scores = {}
            else:
                default_scores = {}
            
            for key, data in additional_criteria.items():
                default_value = default_scores.get(key, 5.0)
                
                # Create badge for criteria type
                badge_html = f'<span class="badge badge-{data["type"]}">{data["type"]}</span>'
                st.markdown(f'{data["description"]} {badge_html}', unsafe_allow_html=True)
                
                additional_scores[key] = st.slider(
                    f"Score for {key}",
                    min_value=0.0,
                    max_value=10.0,
                    value=default_value,
                    step=0.1,
                    key=f"subnet_additional_{key}",
                    label_visibility="collapsed"
                )
        
        # Submit buttons
        if st.session_state.editing_subnet:
            submit_label = "Update Subnet"
            cancel_button = st.checkbox("Cancel editing", value=False)
            if cancel_button:
                st.session_state.editing_subnet = False
                st.session_state.subnet_to_edit = None
        else:
            submit_label = "Add Subnet"
        
        submitted = st.form_submit_button(submit_label, type="primary")
        
        if submitted:
            # Calculate scores
            scores = calculate_scores(
                service_scores,
                research_scores,
                intelligence_scores,
                resource_scores,
                additional_scores,
                {k: v.get('weight', 0.5) for k, v in additional_criteria.items()}
            )
            
            # Create subnet/compass data
            new_data = {
                "name": subnet_name,
                "uid": subnet_uid,
                "description": subnet_description,
                "framework": framework_name,
                "framework_path": framework_data.get('_filepath', ''),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "service_oriented_scores": service_scores,
                "research_oriented_scores": research_scores,
                "intelligence_oriented_scores": intelligence_scores,
                "resource_oriented_scores": resource_scores,
                "additional_criteria_scores": {
                    "scores": additional_scores,
                    "weights": {k: v.get('weight', 0.5) for k, v in additional_criteria.items()}
                },
                "service_research_score": scores.get('service_research_score', (0,0)),
                "intelligence_resource_score": scores.get('intelligence_resource_score', (0,0)),
                "total_score": scores.get('total_score', 0),
                "tier": scores.get('tier', 'N/A')
            }
            
            # If editing, include the ID
            if st.session_state.editing_subnet and subnet_data:
                new_data["id"] = subnet_data.get("id")
            
            # Save to both compass and database for backwards compatibility
            success_subnet = save_subnet(new_data)
            success_compass, compass_path = save_compass(new_data)
            
            # Reset editing state
            st.session_state.editing_subnet = False
            st.session_state.subnet_to_edit = None
            
            # Success message
            if st.session_state.editing_subnet:
                st.success(f"Evaluation '{subnet_name}' updated successfully!")
            else:
                st.success(f"Evaluation '{subnet_name}' created successfully!")
                
                # Show preview of the calculated scores
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Service-Research Score", f"{scores.get('service_research_score', (0,0))}")
                with col2:
                    st.metric("Intelligence-Resource Score", f"{scores.get('intelligence_resource_score', (0,0))}")
                with col3:
                    st.metric("Total Score", f"{scores.get('total_score', 0):.2f}")
                    st.metric("Tier", scores.get('tier', 'N/A'))
            
            # Refresh page
            st.rerun()
    
    # Load compasses as well for the listing
    compasses = load_compasses()
    
    # Display existing subnets (from database) and compasses
    if has_subnets or compasses:
        st.markdown('<h2 class="section-header">Existing Compass Evaluations</h2>', unsafe_allow_html=True)
        
        # Filter out the framework settings entry
        display_df = subnets_df[subnets_df['name'] != "Framework Settings"].copy() if has_subnets else pd.DataFrame()
        
        # Create tabs for Database and File views
        tabs = st.tabs(["All Evaluations", "Database Evaluations", "Compass Files"])
        
        with tabs[0]:
            if not display_df.empty or compasses:
                # Show database entries first if any
                if not display_df.empty:
                    for i, row in display_df.iterrows():
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                tier_class = row['tier'].lower().replace(' ', '-')
                                framework_name = "Unknown Framework"
                                # Try to get framework name from row if it exists
                                if hasattr(row, 'framework') and row.framework:
                                    framework_name = row.framework
                                
                                st.markdown(f"""
                                <div style="margin-bottom: 0.5rem;">
                                    <span style="font-size: 1.2rem; font-weight: 600;">{row['name']}</span>
                                    <span style="margin-left: 1rem; color: #666;">UID: {row['uid']}</span>
                                    <span class="{tier_class}" style="margin-left: 1rem;">{row['tier']}</span>
                                    <span style="margin-left: 1rem; font-size: 0.8rem; color: #888;">[Database]</span>
                                </div>
                                <div style="font-size: 0.9rem; color: #555;">
                                    <p>{row['description']}</p>
                                    <p style="font-size: 0.8rem; color: #777;">Framework: {framework_name}</p>
                                </div>
                                """, unsafe_allow_html=True)
                
                # Show compass file entries
                if compasses:
                    for compass in compasses:
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                tier_class = compass.get('tier', 'unknown').lower().replace(' ', '-')
                                framework_name = compass.get('framework', 'Unknown Framework')
                                
                                st.markdown(f"""
                                <div style="margin-bottom: 0.5rem;">
                                    <span style="font-size: 1.2rem; font-weight: 600;">{compass['name']}</span>
                                    <span style="margin-left: 1rem; color: #666;">UID: {compass.get('uid', 'N/A')}</span>
                                    <span class="{tier_class}" style="margin-left: 1rem;">{compass.get('tier', 'Unknown')}</span>
                                    <span style="margin-left: 1rem; font-size: 0.8rem; color: #888;">[Compass File]</span>
                                </div>
                                <div style="font-size: 0.9rem; color: #555;">
                                    <p>{compass.get('description', 'No description available')}</p>
                                    <p style="font-size: 0.8rem; color: #777;">Framework: {framework_name}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col2:
                                if st.button("Edit", key=f"edit_compass_{compass.get('_filepath', '')}"):
                                    # Get compass data for editing
                                    st.session_state.editing_subnet = True
                                    # Convert compass to subnet-compatible format
                                    subnet_dict = {
                                        "name": compass.get('name', ''),
                                        "uid": compass.get('uid', ''),
                                        "description": compass.get('description', ''),
                                        "service_oriented_scores": compass.get('service_oriented_scores', {}),
                                        "research_oriented_scores": compass.get('research_oriented_scores', {}),
                                        "intelligence_oriented_scores": compass.get('intelligence_oriented_scores', {}),
                                        "resource_oriented_scores": compass.get('resource_oriented_scores', {}),
                                        "additional_criteria_scores": compass.get('additional_criteria_scores', {})
                                    }
                                    st.session_state.subnet_to_edit = subnet_dict
                                    st.session_state.editing_compass_path = compass.get('_filepath', '')
                                    st.rerun()
                            
                            with col3:
                                if st.button("Delete", key=f"delete_compass_{compass.get('_filepath', '')}"):
                                    # Delete confirmation
                                    st.session_state[f"confirm_delete_compass_{compass.get('_filepath', '')}"] = True
                            
                            # Show delete confirmation
                            if st.session_state.get(f"confirm_delete_compass_{compass.get('_filepath', '')}", False):
                                confirm_col1, confirm_col2 = st.columns([1, 1])
                                with confirm_col1:
                                    if st.button("Yes, Delete", key=f"confirm_yes_compass_{compass.get('_filepath', '')}"):
                                        delete_compass(compass.get('_filepath', ''))
                                        # Clear state
                                        del st.session_state[f"confirm_delete_compass_{compass.get('_filepath', '')}"]
                                        st.success(f"Compass '{compass['name']}' deleted successfully!")
                                        st.rerun()
                                
                                with confirm_col2:
                                    if st.button("Cancel", key=f"confirm_no_compass_{compass.get('_filepath', '')}"):
                                        # Clear state
                                        del st.session_state[f"confirm_delete_compass_{compass.get('_filepath', '')}"]
                                        st.rerun()
                            
                            st.markdown("---")
            else:
                st.info("No subnet evaluations found. Create a new evaluation using the form above.")
        
        with tabs[1]:
            if not display_df.empty:
                # Create a container for each subnet with action buttons
                for i, row in display_df.iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            tier_class = row['tier'].lower().replace(' ', '-')
                            st.markdown(f"""
                            <div style="margin-bottom: 0.5rem;">
                                <span style="font-size: 1.2rem; font-weight: 600;">{row['name']}</span>
                                <span style="margin-left: 1rem; color: #666;">UID: {row['uid']}</span>
                                <span class="{tier_class}" style="margin-left: 1rem;">{row['tier']}</span>
                            </div>
                            <div style="font-size: 0.9rem; color: #555;">{row['description']}</div>
                            """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("Edit", key=f"edit_{row['id']}"):
                            # Convert row to dictionary for editing
                            subnet_dict = row.to_dict()
                            # Convert scores back to dictionaries if they're strings
                            for col in ['service_oriented_scores', 'research_oriented_scores', 
                                      'intelligence_oriented_scores', 'resource_oriented_scores',
                                      'additional_criteria_scores']:
                                if isinstance(subnet_dict[col], str):
                                    subnet_dict[col] = json.loads(subnet_dict[col])
                            
                            st.session_state.editing_subnet = True
                            st.session_state.subnet_to_edit = subnet_dict
                            st.rerun()
                    
                    with col3:
                        if st.button("Delete", key=f"delete_{row['id']}"):
                            # Delete confirmation
                            st.session_state[f"confirm_delete_{row['id']}"] = True
                    
                    # Show delete confirmation
                    if st.session_state.get(f"confirm_delete_{row['id']}", False):
                        confirm_col1, confirm_col2 = st.columns([1, 1])
                        with confirm_col1:
                            if st.button("Yes, Delete", key=f"confirm_yes_{row['id']}"):
                                delete_subnet(row['id'])
                                # Clear state
                                del st.session_state[f"confirm_delete_{row['id']}"]
                                st.success(f"Subnet '{row['name']}' deleted successfully!")
                                st.rerun()
                        
                        with confirm_col2:
                            if st.button("Cancel", key=f"confirm_no_{row['id']}"):
                                # Clear state
                                del st.session_state[f"confirm_delete_{row['id']}"]
                                st.rerun()
                
                st.markdown("---")
            
            # Compass Files Tab
            with tabs[2]:
                if compasses:
                    for compass in compasses:
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                tier_class = compass.get('tier', 'unknown').lower().replace(' ', '-')
                                framework_name = compass.get('framework', 'Unknown Framework')
                                
                                st.markdown(f"""
                                <div style="margin-bottom: 0.5rem;">
                                    <span style="font-size: 1.2rem; font-weight: 600;">{compass['name']}</span>
                                    <span style="margin-left: 1rem; color: #666;">UID: {compass.get('uid', 'N/A')}</span>
                                    <span class="{tier_class}" style="margin-left: 1rem;">{compass.get('tier', 'Unknown')}</span>
                                </div>
                                <div style="font-size: 0.9rem; color: #555;">
                                    <p>{compass.get('description', 'No description available')}</p>
                                    <p style="font-size: 0.8rem; color: #777;">Framework: {framework_name}</p>
                                    <p style="font-size: 0.8rem; color: #777;">File: {compass.get('_filepath', 'Unknown')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col2:
                                if st.button("Edit", key=f"edit_compass_tab2_{compass.get('_filepath', '')}"):
                                    # Get compass data for editing
                                    st.session_state.editing_subnet = True
                                    # Convert compass to subnet-compatible format
                                    subnet_dict = {
                                        "name": compass.get('name', ''),
                                        "uid": compass.get('uid', ''),
                                        "description": compass.get('description', ''),
                                        "service_oriented_scores": compass.get('service_oriented_scores', {}),
                                        "research_oriented_scores": compass.get('research_oriented_scores', {}),
                                        "intelligence_oriented_scores": compass.get('intelligence_oriented_scores', {}),
                                        "resource_oriented_scores": compass.get('resource_oriented_scores', {}),
                                        "additional_criteria_scores": compass.get('additional_criteria_scores', {})
                                    }
                                    st.session_state.subnet_to_edit = subnet_dict
                                    st.session_state.editing_compass_path = compass.get('_filepath', '')
                                    st.rerun()
                            
                            with col3:
                                if st.button("Delete", key=f"delete_compass_tab2_{compass.get('_filepath', '')}"):
                                    # Delete confirmation
                                    st.session_state[f"confirm_delete_compass_tab2_{compass.get('_filepath', '')}"] = True
                            
                            # Show delete confirmation
                            if st.session_state.get(f"confirm_delete_compass_tab2_{compass.get('_filepath', '')}", False):
                                confirm_col1, confirm_col2 = st.columns([1, 1])
                                with confirm_col1:
                                    if st.button("Yes, Delete", key=f"confirm_yes_compass_tab2_{compass.get('_filepath', '')}"):
                                        delete_compass(compass.get('_filepath', ''))
                                        # Clear state
                                        del st.session_state[f"confirm_delete_compass_tab2_{compass.get('_filepath', '')}"]
                                        st.success(f"Compass '{compass['name']}' deleted successfully!")
                                        st.rerun()
                                
                                with confirm_col2:
                                    if st.button("Cancel", key=f"confirm_no_compass_tab2_{compass.get('_filepath', '')}"):
                                        # Clear state
                                        del st.session_state[f"confirm_delete_compass_tab2_{compass.get('_filepath', '')}"]
                                        st.rerun()
                            
                            st.markdown("---")
                else:
                    st.info("No compass evaluation files found.")
            
            # Navigation buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Go to Visualization", type="secondary"):
                    st.session_state['active_page'] = "visualization"
                    st.rerun()

def visualization_page():
    """Page for visualizing subnet data."""
    st.markdown('<h1 class="main-header">Subnet Visualization</h1>', unsafe_allow_html=True)
    
    # Get subnets data
    subnets_df = get_subnets()
    
    # Check if there are subnets to visualize (excluding the Framework Settings entry)
    display_df = subnets_df[subnets_df['name'] != "Framework Settings"].copy()
    
    if display_df.empty:
        st.warning("No subnets found for visualization. Please add subnets first.")
        return
    
    # Initialize session state for subnet selection if not already set
    if 'selected_subnets' not in st.session_state:
        st.session_state['selected_subnets'] = {row['name']: True for _, row in display_df.iterrows()}
        
    # Add subnet selection interface (checkboxes)
    st.markdown('<h3>Select Subnets to Display</h3>', unsafe_allow_html=True)
    
    # Add custom CSS for checkbox grid
    st.markdown("""
    <style>
    .checkbox-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }
    .checkbox-item {
        flex: 0 0 30%;  /* Adjust to control width */
        margin-bottom: 5px;
    }
    .stButton {
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Select/Deselect All buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Select All", key="select_all_btn"):
            for name in st.session_state['selected_subnets']:
                st.session_state['selected_subnets'][name] = True
            st.rerun()
            
    with col2:
        if st.button("Deselect All", key="deselect_all_btn"):
            for name in st.session_state['selected_subnets']:
                st.session_state['selected_subnets'][name] = False
            st.rerun()
    
    # Create checkbox grid with 3 columns
    checkbox_cols = st.columns(3)
    
    for i, (_, row) in enumerate(display_df.iterrows()):
        subnet_name = row['name']
        col_idx = i % 3
        
        with checkbox_cols[col_idx]:
            st.session_state['selected_subnets'][subnet_name] = st.checkbox(
                subnet_name, 
                value=st.session_state['selected_subnets'].get(subnet_name, True),
                key=f"subnet_checkbox_{subnet_name}"
            )
    
    # Filter the dataframe based on selected subnets
    selected_names = [name for name, selected in st.session_state['selected_subnets'].items() if selected]
    filtered_df = display_df[display_df['name'].isin(selected_names)].copy()
    
    # Calculate scores for the dashboards
    for i, row in filtered_df.iterrows():
        # Ensure these are dictionaries
        service_scores = row['service_oriented_scores']
        research_scores = row['research_oriented_scores'] 
        intelligence_scores = row['intelligence_oriented_scores']
        resource_scores = row['resource_oriented_scores']
        
        # Calculate averages
        filtered_df.at[i, 'service_avg'] = sum(service_scores.values()) / len(service_scores) if service_scores else 0
        filtered_df.at[i, 'research_avg'] = sum(research_scores.values()) / len(research_scores) if research_scores else 0
        filtered_df.at[i, 'intelligence_avg'] = sum(intelligence_scores.values()) / len(intelligence_scores) if intelligence_scores else 0
        filtered_df.at[i, 'resource_avg'] = sum(resource_scores.values()) / len(resource_scores) if resource_scores else 0
    
    # Show warning if no subnets are selected
    if filtered_df.empty:
        st.warning("No subnets selected for visualization. Please select at least one subnet.")
        return
    
    # Create tabs for different visualizations
    tabs = st.tabs(["Quadrant Charts", "Subnet Scores", "Detailed Analysis", "Comparison", "Score Matrix"])
    
    # Quadrant Charts
    with tabs[0]:
        st.markdown('<h2 class="section-header">Subnet Positioning</h2>', unsafe_allow_html=True)
        
        # Create two columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<h3 class="subsection-header">Service vs Research Orientation</h3>', unsafe_allow_html=True)
            fig = create_quadrant_chart(filtered_df, "service_research")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown('<h3 class="subsection-header">Intelligence vs Resource Orientation</h3>', unsafe_allow_html=True)
            fig = create_quadrant_chart(filtered_df, "intelligence_resource")
            st.plotly_chart(fig, use_container_width=True)
    
    # Subnet Scores
    with tabs[1]:
        st.markdown('<h2 class="section-header">Subnet Scores</h2>', unsafe_allow_html=True)
        
        # Create score chart
        fig = create_score_chart(filtered_df)
        st.plotly_chart(fig, use_container_width=True)
        
        # Create a table of scores
        st.markdown('<h3 class="subsection-header">Score Breakdown</h3>', unsafe_allow_html=True)
        
        # Prepare data for table
        table_data = []
        for i, row in filtered_df.iterrows():
            table_data.append({
                "Subnet": row['name'],
                "UID": row['uid'],
                "Service Score": f"{row['service_avg']:.1f}",
                "Research Score": f"{row['research_avg']:.1f}",
                "Intelligence Score": f"{row['intelligence_avg']:.1f}",
                "Resource Score": f"{row['resource_avg']:.1f}",
                "Total Score": f"{row['total_score']:.1f}",
                "Tier": row['tier']
            })
        
        # Convert to DataFrame for display
        table_df = pd.DataFrame(table_data)
        
        # Style the table based on tier
        def highlight_tier(val):
            if val == "Tier A":
                return 'background-color: rgba(61, 197, 189, 0.2); color: #3dc5bd; font-weight: bold'
            elif val == "Tier B":
                return 'background-color: rgba(88, 132, 197, 0.2); color: #5884c5; font-weight: bold'
            elif val == "Tier C":
                return 'background-color: rgba(244, 190, 85, 0.2); color: #f4be55; font-weight: bold'
            elif val == "Tier D":
                return 'background-color: rgba(255, 159, 100, 0.2); color: #ff9f64; font-weight: bold'
            return ''
        
        # Apply styling and display table
        styled_table = table_df.style.map(highlight_tier, subset=['Tier'])
        st.dataframe(styled_table, use_container_width=True)
    
    # Detailed Analysis
    with tabs[2]:
        st.markdown('<h2 class="section-header">Detailed Subnet Analysis</h2>', unsafe_allow_html=True)
        
        # Subnet selector
        selected_subnet = st.selectbox(
            "Select Subnet for Analysis",
            filtered_df['name'].tolist(),
            key="detailed_analysis_subnet"
        )
        
        # Get selected subnet data
        subnet_data = filtered_df[filtered_df['name'] == selected_subnet].iloc[0]
        
        # Create columns for subnet info and scores
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown('<h3 class="subsection-header">Subnet Information</h3>', unsafe_allow_html=True)
            
            # Format tier with appropriate class
            tier_class = subnet_data['tier'].lower().replace(' ', '-')
            
            st.markdown(f"""
            <div class="custom-info-box">
                <p><strong>Name:</strong> {subnet_data['name']}</p>
                <p><strong>UID:</strong> {subnet_data['uid']}</p>
                <p><strong>Tier:</strong> <span class="{tier_class}">{subnet_data['tier']}</span></p>
                <p><strong>Total Score:</strong> {subnet_data['total_score']:.1f}</p>
                <p><strong>Description:</strong> {subnet_data['description']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown('<h3 class="subsection-header">Score Breakdown</h3>', unsafe_allow_html=True)
            
            # Create radar chart
            fig = create_radar_chart(subnet_data)
            st.plotly_chart(fig, use_container_width=True)
        
        # Create tabs for detailed criteria scores
        criteria_tabs = st.tabs(["Service", "Research", "Intelligence", "Resource", "Additional"])
        
        # Service criteria
        with criteria_tabs[0]:
            create_criteria_scores_table(subnet_data, 'service_oriented_scores', "Service-Oriented Criteria")
        
        # Research criteria
        with criteria_tabs[1]:
            create_criteria_scores_table(subnet_data, 'research_oriented_scores', "Research-Oriented Criteria")
        
        # Intelligence criteria
        with criteria_tabs[2]:
            create_criteria_scores_table(subnet_data, 'intelligence_oriented_scores', "Intelligence-Oriented Criteria")
        
        # Resource criteria
        with criteria_tabs[3]:
            create_criteria_scores_table(subnet_data, 'resource_oriented_scores', "Resource-Oriented Criteria")
        
        # Additional criteria
        with criteria_tabs[4]:
            if isinstance(subnet_data['additional_criteria_scores'], dict) and 'scores' in subnet_data['additional_criteria_scores']:
                scores = subnet_data['additional_criteria_scores']['scores']
                weights = subnet_data['additional_criteria_scores'].get('weights', {})
                create_additional_criteria_scores_table(scores, weights, "Additional Evaluation Criteria")
            else:
                st.info("No additional criteria scores available.")
    
    # Comparison
    with tabs[3]:
        st.markdown('<h2 class="section-header">Subnet Comparison</h2>', unsafe_allow_html=True)
        
        # Multi-select for subnets to compare
        selected_subnets = st.multiselect(
            "Select Subnets to Compare",
            filtered_df['name'].tolist(),
            default=filtered_df['name'].tolist()[:2] if len(filtered_df) >= 2 else filtered_df['name'].tolist(),
            key="comparison_subnets"
        )
        
        if len(selected_subnets) < 2:
            st.warning("Please select at least 2 subnets to compare.")
            return
        
        # Filter dataframe for selected subnets
        compare_df = filtered_df[filtered_df['name'].isin(selected_subnets)]
        
        # Create comparison chart
        fig = create_comparison_chart(compare_df)
        st.plotly_chart(fig, use_container_width=True)
        
        # Create detailed comparison table
        st.markdown('<h3 class="subsection-header">Detailed Comparison</h3>', unsafe_allow_html=True)
        
        # Get main criteria categories
        criteria = get_evaluation_criteria()
        all_criteria = {}
        
        for category, items in criteria.items():
            for key, description in items.items():
                all_criteria[f"{category}_{key}"] = description
        
        # Create comparison data
        comparison_data = []
        
        for i, row in compare_df.iterrows():
            subnet_scores = {}
            subnet_scores["Subnet"] = row['name']
            
            # Add main criteria scores
            for category in ['service', 'research', 'intelligence', 'resource']:
                for key in criteria[category].keys():
                    score_dict = row[f'{category}_oriented_scores']
                    subnet_scores[f"{category}_{key}"] = score_dict.get(key, 0)
            
            # Add to comparison data
            comparison_data.append(subnet_scores)
        
        # Convert to DataFrame
        comparison_df = pd.DataFrame(comparison_data)
        
        # Create a transposed view for better comparison
        comparison_df = comparison_df.set_index('Subnet').T.reset_index()
        comparison_df = comparison_df.rename(columns={'index': 'Criteria'})
        
        # Map criteria codes to descriptions
        comparison_df['Description'] = comparison_df['Criteria'].map(
            lambda x: all_criteria.get(x, x)
        )
        
        # Reorder columns to put description first
        cols = comparison_df.columns.tolist()
        cols.remove('Description')
        cols.remove('Criteria')
        comparison_df = comparison_df[['Criteria', 'Description'] + cols]
        
        # Style the dataframe
        def color_scale(val):
            if isinstance(val, (int, float)):
                # Scale from 0 to 10
                color_val = int(val * 25.5)  # Scale to 0-255
                return f'background-color: rgba({255-color_val}, {color_val}, 100, 0.2)'
            return ''
        
        # Apply styling and display
        styled_comparison = comparison_df.style.map(color_scale, subset=compare_df['name'].tolist())
        st.dataframe(styled_comparison, use_container_width=True)
        
    # Score Matrix (Excel-like view)
    with tabs[4]:
        st.markdown('<h2 class="section-header">Subnet Score Matrix</h2>', unsafe_allow_html=True)
        
        # Get criteria categories
        criteria = get_evaluation_criteria()
        
        # Radio buttons for category selection
        category_options = ["Service", "Research", "Intelligence", "Resource", "Additional"]
        selected_category = st.radio("Select Category", category_options, horizontal=True)
        
        # Convert to lowercase for dict keys
        category_key = selected_category.lower()
        
        if category_key == "additional":
            # Create matrix for additional criteria
            st.markdown(f"<h3 class='subsection-header'>{selected_category} Criteria Scores</h3>", unsafe_allow_html=True)
            
            # Get criteria names
            additional_criteria = get_additional_evaluation_criteria()
            criteria_keys = list(additional_criteria.keys())
            
            # Create matrix data
            matrix_data = {}
            # First column will be criteria questions
            matrix_data["Criteria"] = [criteria.get("question", key) for key, criteria in additional_criteria.items()]
            
            # Add each subnet as a column
            for _, row in filtered_df.iterrows():
                subnet_name = row['name']
                additional_scores = row.get('additional_criteria_scores', {})
                
                if isinstance(additional_scores, dict) and 'scores' in additional_scores:
                    scores = additional_scores['scores']
                    matrix_data[subnet_name] = [scores.get(key, "N/A") for key in criteria_keys]
                else:
                    # If no scores available, fill with N/A
                    matrix_data[subnet_name] = ["N/A"] * len(criteria_keys)
            
            # Convert to DataFrame
            matrix_df = pd.DataFrame(matrix_data)
            
            # Style function for scores
            def color_score(val):
                if isinstance(val, (int, float)):
                    # Determine color based on score (0-10 scale)
                    if val >= 7.5:
                        return 'background-color: rgba(0, 200, 0, 0.2); color: #006400'
                    elif val >= 5:
                        return 'background-color: rgba(200, 200, 0, 0.2); color: #7a7a00'
                    elif val >= 2.5:
                        return 'background-color: rgba(255, 165, 0, 0.2); color: #cc5500'
                    else:
                        return 'background-color: rgba(255, 0, 0, 0.2); color: #8b0000'
                return ''
            
            # Apply styling to all columns except the first (criteria names)
            styled_matrix = matrix_df.style.map(color_score, subset=[col for col in matrix_df.columns if col != "Criteria"])
            
            # Display styled matrix
            st.dataframe(styled_matrix, use_container_width=True)
            
        else:
            # Create matrix for main criteria categories
            st.markdown(f"<h3 class='subsection-header'>{selected_category}-Oriented Criteria Scores</h3>", unsafe_allow_html=True)
            
            # Get criteria questions
            category_criteria = criteria.get(category_key, {})
            criteria_keys = list(category_criteria.keys())
            
            # Create matrix data
            matrix_data = {}
            # First column will be criteria questions
            matrix_data["Criteria"] = [data.get("question", key) if isinstance(data, dict) else data 
                                     for key, data in category_criteria.items()]
            
            # Add each subnet as a column
            for _, row in filtered_df.iterrows():
                subnet_name = row['name']
                scores_key = f"{category_key}_oriented_scores"
                scores = row.get(scores_key, {})
                
                matrix_data[subnet_name] = [scores.get(key, "N/A") for key in criteria_keys]
            
            # Convert to DataFrame
            matrix_df = pd.DataFrame(matrix_data)
            
            # Style function for scores
            def color_score(val):
                if isinstance(val, (int, float)):
                    # Determine color based on score (0-10 scale)
                    if val >= 7.5:
                        return 'background-color: rgba(0, 200, 0, 0.2); color: #006400'
                    elif val >= 5:
                        return 'background-color: rgba(200, 200, 0, 0.2); color: #7a7a00'
                    elif val >= 2.5:
                        return 'background-color: rgba(255, 165, 0, 0.2); color: #cc5500'
                    else:
                        return 'background-color: rgba(255, 0, 0, 0.2); color: #8b0000'
                return ''
            
            # Apply styling to all columns except the first (criteria names)
            styled_matrix = matrix_df.style.map(color_score, subset=[col for col in matrix_df.columns if col != "Criteria"])
            
            # Display styled matrix
            st.dataframe(styled_matrix, use_container_width=True)


# Visualization functions
def create_quadrant_chart(df, chart_type):
    """Create a quadrant chart."""
    # Set up chart data based on type
    if chart_type == "service_research":
        x_title = "Research Orientation"
        y_title = "Service Orientation"
        
        # Transform values to -10 to 10 scale for plotting
        x_values = [(2 * df['research_avg'] - 10).tolist()]
        y_values = [(2 * df['service_avg'] - 10).tolist()]
        
        quadrant_labels = ["Research-Focused", "Full-Spectrum", "Balanced", "Service-Focused"]
    else:  # intelligence_resource
        x_title = "Resource Orientation"
        y_title = "Intelligence Orientation"
        
        # Transform values to -10 to 10 scale for plotting
        x_values = [(2 * df['resource_avg'] - 10).tolist()]
        y_values = [(2 * df['intelligence_avg'] - 10).tolist()]
        
        quadrant_labels = ["Resource-Focused", "Full-Spectrum", "Balanced", "Intelligence-Focused"]
    
    # Prepare data for scatter plot
    names = df['name'].tolist()
    tiers = df['tier'].tolist()
    
    # Color mapping for tiers
    color_map = {
        "Tier A": "#3dc5bd",
        "Tier B": "#5884c5",
        "Tier C": "#f4be55", 
        "Tier D": "#ff9f64"
    }
    
    colors = [color_map.get(tier, "#aaaaaa") for tier in tiers]
    
    # Set up hover text
    hover_texts = []
    for i, row in df.iterrows():
        hover_text = f"<b>{row['name']}</b><br>"
        hover_text += f"UID: {row['uid']}<br>"
        hover_text += f"Tier: {row['tier']}<br>"
        hover_text += f"Total Score: {row['total_score']:.1f}<br>"
        
        if chart_type == "service_research":
            hover_text += f"Service: {row['service_avg']:.1f}<br>"
            hover_text += f"Research: {row['research_avg']:.1f}<br>"
        else:
            hover_text += f"Intelligence: {row['intelligence_avg']:.1f}<br>"
            hover_text += f"Resource: {row['resource_avg']:.1f}<br>"
        
        hover_text += f"Description: {row['description']}"
        hover_texts.append(hover_text)
    
    # Create figure
    fig = go.Figure()
    
    # Add scatter plot
    fig.add_trace(go.Scatter(
        x=x_values[0],
        y=y_values[0],
        mode='markers+text',
        text=names,
        textposition='top center',
        marker=dict(
            size=14,
            color=colors,
            line=dict(width=2, color='white')
        ),
        hoverinfo='text',
        hovertext=hover_texts,
        textfont=dict(
            family="Arial",
            size=11,
        )
    ))
    
    # Add quadrant lines
    fig.add_shape(
        type="line",
        x0=-10, y0=0,
        x1=10, y1=0,
        line=dict(color="gray", width=1, dash="dash")
    )
    
    fig.add_shape(
        type="line",
        x0=0, y0=-10,
        x1=0, y1=10,
        line=dict(color="gray", width=1, dash="dash")
    )
    
    # Add quadrant labels
    fig.add_annotation(x=5, y=5, text=quadrant_labels[1], showarrow=False, font=dict(size=12))
    fig.add_annotation(x=-5, y=5, text=quadrant_labels[0], showarrow=False, font=dict(size=12))
    fig.add_annotation(x=-5, y=-5, text=quadrant_labels[2], showarrow=False, font=dict(size=12))
    fig.add_annotation(x=5, y=-5, text=quadrant_labels[3], showarrow=False, font=dict(size=12))
    
    # Update layout
    fig.update_layout(
        title=f"{y_title} vs {x_title}",
        xaxis=dict(
            title=x_title,
            range=[-11, 11],
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='black',
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title=y_title,
            range=[-11, 11],
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='black',
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        height=600,
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode='closest'
    )
    
    return fig

def create_score_chart(df):
    """Create a bar chart of subnet scores."""
    # Sort by total score
    sorted_df = df.sort_values(by='total_score', ascending=False).copy()
    
    # Get tier colors
    tier_colors = {
        "Tier A": "#3dc5bd",
        "Tier B": "#5884c5",
        "Tier C": "#f4be55",
        "Tier D": "#ff9f64"
    }
    
    # Create color list based on tiers
    colors = [tier_colors.get(tier, "#aaaaaa") for tier in sorted_df['tier']]
    
    # Create figure
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(go.Bar(
        x=sorted_df['name'],
        y=sorted_df['total_score'],
        marker_color=colors,
        text=[f"{score:.1f}" for score in sorted_df['total_score']],
        textposition='auto',
        hovertemplate="<b>%{x}</b><br>" +
                      "Total Score: %{y:.1f}<br>" +
                      "Tier: %{customdata}<extra></extra>",
        customdata=sorted_df['tier']
    ))
    
    # Add tier regions
    fig.add_shape(
        type="rect",
        x0=-0.5, x1=len(sorted_df)-0.5, y0=8.5, y1=10,
        fillcolor="rgba(61, 197, 189, 0.2)",
        line=dict(width=0),
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=-0.5, x1=len(sorted_df)-0.5, y0=7, y1=8.5,
        fillcolor="rgba(88, 132, 197, 0.2)",
        line=dict(width=0),
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=-0.5, x1=len(sorted_df)-0.5, y0=5.5, y1=7,
        fillcolor="rgba(244, 190, 85, 0.2)",
        line=dict(width=0),
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=-0.5, x1=len(sorted_df)-0.5, y0=0, y1=5.5,
        fillcolor="rgba(255, 159, 100, 0.2)",
        line=dict(width=0),
        layer="below"
    )
    
    # Add tier labels
    fig.add_annotation(
        x=len(sorted_df)-1,
        y=9.25,
        text="Tier A",
        showarrow=False,
        font=dict(color="#3dc5bd", size=14),
        align="right",
        xanchor="right"
    )
    
    fig.add_annotation(
        x=len(sorted_df)-1,
        y=7.75,
        text="Tier B",
        showarrow=False,
        font=dict(color="#5884c5", size=14),
        align="right",
        xanchor="right"
    )
    
    fig.add_annotation(
        x=len(sorted_df)-1,
        y=6.25,
        text="Tier C",
        showarrow=False,
        font=dict(color="#f4be55", size=14),
        align="right",
        xanchor="right"
    )
    
    fig.add_annotation(
        x=len(sorted_df)-1,
        y=2.75,
        text="Tier D",
        showarrow=False,
        font=dict(color="#ff9f64", size=14),
        align="right",
        xanchor="right"
    )
    
    # Update layout
    fig.update_layout(
        title="Subnet Total Scores",
        xaxis_title="Subnet",
        yaxis_title="Score",
        yaxis=dict(range=[0, 10]),
        plot_bgcolor='white',
        height=500,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    return fig

def create_radar_chart(subnet_data):
    """Create a radar chart for a subnet."""
    # Get category averages
    service_avg = subnet_data['service_avg']
    research_avg = subnet_data['research_avg']
    intelligence_avg = subnet_data['intelligence_avg']
    resource_avg = subnet_data['resource_avg']
    
    # Get scores for detailed categories
    service_scores = subnet_data['service_oriented_scores']
    research_scores = subnet_data['research_oriented_scores']
    intelligence_scores = subnet_data['intelligence_oriented_scores']
    resource_scores = subnet_data['resource_oriented_scores']
    
    # Get evaluation criteria for proper labeling
    criteria = get_evaluation_criteria()
    
    # Prepare data for radar chart
    categories = []
    values = []
    
    # Service criteria
    for key, desc in criteria['service'].items():
        categories.append(f"Srv: {desc[:20]}...")
        values.append(service_scores.get(key, 0))
    
    # Research criteria
    for key, desc in criteria['research'].items():
        categories.append(f"Res: {desc[:20]}...")
        values.append(research_scores.get(key, 0))
    
    # Intelligence criteria
    for key, desc in criteria['intelligence'].items():
        categories.append(f"Int: {desc[:20]}...")
        values.append(intelligence_scores.get(key, 0))
    
    # Resource criteria
    for key, desc in criteria['resource'].items():
        categories.append(f"Rsc: {desc[:20]}...")
        values.append(resource_scores.get(key, 0))
    
    # Close the loop for radar chart
    categories.append(categories[0])
    values.append(values[0])
    
    # Create figure
    fig = go.Figure()
    
    # Add radar chart
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(77, 104, 233, 0.2)',
        line=dict(color='#4d68e9'),
        name=subnet_data['name']
    ))
    
    # Create another trace for category averages
    avg_categories = ['Service', 'Research', 'Intelligence', 'Resource', 'Service']
    avg_values = [service_avg, research_avg, intelligence_avg, resource_avg, service_avg]
    
    fig.add_trace(go.Scatterpolar(
        r=avg_values,
        theta=avg_categories,
        fill='toself',
        fillcolor='rgba(255, 75, 75, 0.2)',
        line=dict(color='#ff4b4b', width=3, dash='dash'),
        name='Category Averages'
    ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        height=500,
        title=f"Subnet Profile: {subnet_data['name']}",
        showlegend=True
    )
    
    return fig

def create_criteria_scores_table(subnet_data, scores_field, title):
    """Create a table of criteria scores."""
    scores = subnet_data[scores_field]
    
    if not scores:
        st.info(f"No {title} scores available.")
        return
    
    # Get criteria descriptions
    criteria_type = scores_field.split('_')[0]
    criteria = get_evaluation_criteria()[criteria_type]
    
    # Create table data
    table_data = []
    for key, description in criteria.items():
        score = scores.get(key, 0)
        table_data.append({
            "Criteria": description,
            "Score": score
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(table_data)
    
    # Calculate category average
    avg_score = sum(scores.values()) / len(scores) if scores else 0
    
    # Display table with header
    st.markdown(f'<h4>{title} (Average: {avg_score:.1f})</h4>', unsafe_allow_html=True)
    
    # Style the dataframe
    def color_score(val):
        if isinstance(val, (int, float)):
            # Scale from 0 to 10
            color_val = int(val * 25.5)  # Scale to 0-255
            return f'background-color: rgba({255-color_val}, {color_val}, 100, 0.2)'
        return ''
    
    # Apply styling and display
    styled_df = df.style.map(color_score, subset=['Score'])
    st.dataframe(styled_df, use_container_width=True)

def create_additional_criteria_scores_table(scores, weights, title):
    """Create a table of additional criteria scores."""
    if not scores:
        st.info(f"No {title} scores available.")
        return
    
    # Get criteria descriptions
    criteria = get_additional_evaluation_criteria()
    
    # Create table data
    table_data = []
    for key, value in scores.items():
        if key in criteria:
            description = criteria[key]['description']
            criteria_type = criteria[key]['type']
            weight = weights.get(key, {}).get('weight', criteria[key]['weight']) if weights else criteria[key]['weight']
            
            # Determine impact based on type and score
            impact = 0
            if criteria_type == 'positive':
                impact = value * weight / 10  # Scale to 0-1
            elif criteria_type == 'negative':
                impact = -value * weight / 10  # Negative impact
            else:  # bidirectional
                if value >= 5:
                    impact = (value - 5) * weight / 5  # Positive impact, scaled to 0-1
                else:
                    impact = -(5 - value) * weight / 5  # Negative impact, scaled to 0-1
            
            table_data.append({
                "Criteria": description,
                "Type": criteria_type.capitalize(),
                "Weight": weight,
                "Score": value,
                "Impact": impact
            })
    
    # Convert to DataFrame
    df = pd.DataFrame(table_data)
    
    # Display table with header
    st.markdown(f'<h4>{title}</h4>', unsafe_allow_html=True)
    
    # Style the dataframe
    def color_score(val):
        if isinstance(val, (int, float)):
            # Scale from 0 to 10
            color_val = int(val * 25.5)  # Scale to 0-255
            return f'background-color: rgba({255-color_val}, {color_val}, 100, 0.2)'
        return ''
    
    def color_impact(val):
        if isinstance(val, (int, float)):
            if val > 0:
                # Positive impact - green scale
                intensity = min(int(abs(val) * 255), 255)
                return f'background-color: rgba(0, {intensity}, 0, 0.2); color: green;'
            elif val < 0:
                # Negative impact - red scale
                intensity = min(int(abs(val) * 255), 255)
                return f'background-color: rgba({intensity}, 0, 0, 0.2); color: darkred;'
        return ''
    
    def color_type(val):
        if val == 'Positive':
            return 'background-color: rgba(40, 167, 69, 0.2); color: #28a745;'
        elif val == 'Negative':
            return 'background-color: rgba(220, 53, 69, 0.2); color: #dc3545;'
        elif val == 'Bidirectional':
            return 'background-color: rgba(255, 193, 7, 0.2); color: #000;'
        return ''
    
    # Apply styling and display
    styled_df = df.style.map(color_score, subset=['Score']) \
                       .map(color_impact, subset=['Impact']) \
                       .map(color_type, subset=['Type']) \
                       .format({'Weight': '{:.1f}', 'Score': '{:.1f}', 'Impact': '{:.2f}'})
    
    st.dataframe(styled_df, use_container_width=True)

def create_comparison_chart(df):
    """Create a radar chart comparing multiple subnets."""
    # Get evaluation criteria
    criteria = get_evaluation_criteria()
    
    # Create figure
    fig = go.Figure()
    
    # Categories for the radar chart (use the main categories)
    categories = ['Service', 'Research', 'Intelligence', 'Resource', 'Service']  # Close the loop
    
    # Color palette for different subnets
    colors = px.colors.qualitative.Plotly
    
    # Add a trace for each subnet
    for i, (idx, row) in enumerate(df.iterrows()):
        values = [
            row['service_avg'], 
            row['research_avg'], 
            row['intelligence_avg'], 
            row['resource_avg'],
            row['service_avg']  # Close the loop
        ]
        
        color = colors[i % len(colors)]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            fillcolor=f'rgba{tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (0.2,)}',
            line=dict(color=color),
            name=row['name']
        ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        title="Subnet Comparison",
        height=600
    )
    
    return fig

# Example subnet initialization
def load_example_subnets():
    """Load example subnets for the Sherpa Framework."""
    # Clear existing data
    clear_all_subnets()
    
    # Get additional criteria weights
    additional_criteria_data = get_additional_evaluation_criteria()
    
    # Convertir los criterios adicionales al formato correcto para almacenar
    weights_data = {}
    for key, data in additional_criteria_data.items():
        weights_data[key] = {
            "weight": data["weight"],
            "type": data["type"]
        }
    
    # Define example subnets
    example_subnets = [
        {
            "name": "3gen",
            "uid": "17",
            "description": "A next-generation subnet with custom evaluation score of 1.4.",
            "service_oriented_scores": {
                "functioning_product": 7,
                "immediate_utility": 6,
                "revenue_model": 7,
                "apis_integrations": 6,
                "validator_monetization": 7,
                "usage_metrics": 6,
                "implementation_docs": 7,
                "real_world_use_cases": 6
            },
            "research_oriented_scores": {
                "fundamental_problems": 5,
                "academic_publications": 4,
                "research_background": 5,
                "technical_roadmap": 6,
                "academic_collaboration": 3,
                "emerging_tech": 7,
                "scientific_goals": 5
            },
            "intelligence_oriented_scores": {
                "intelligent_processing": 8,
                "specialized_expertise": 7,
                "new_insights": 6,
                "intellectual_barrier": 5,
                "learning_improvement": 7
            },
            "resource_oriented_scores": {
                "computational_value": 5,
                "hardware_requirements": 6,
                "resource_provider": 5,
                "geographic_importance": 4,
                "redundancy_value": 5,
                "resource_returns": 6
            },
            "additional_criteria_scores": {
                "scores": {
                    "substrate_registration": 4,
                    "current_revenue": 1,
                    "revenue_prospects": 3,
                    "team_quantifiable": 2,
                    "team_track_record": 2,
                    "competitive_viability": 4,
                    "total_addressable_market": 3,
                    "roadmap_quality": 1,
                    "documentation_quality": 0,
                    "ui_ux_quality": 1,
                    "github_activity": 0.5,
                    "twitter_activity": 0.5,
                    "dtao_marketing": 0,
                    "third_party_integrations": 1,
                    "partnerships": 1,
                    "subnet_uniqueness": 2,
                    "interoperability": 0,
                    "miner_rewards": 0,
                    "subnet_integration": 1
                },
                "weights": weights_data
            }
        },
        {
            "name": "pτn",
            "uid": "8",
            "description": "Pioneering subnet with a custom evaluation score of 3.2.",
            "service_oriented_scores": {
                "functioning_product": 7,
                "immediate_utility": 8,
                "revenue_model": 7,
                "apis_integrations": 7,
                "validator_monetization": 8,
                "usage_metrics": 7,
                "implementation_docs": 8,
                "real_world_use_cases": 7
            },
            "research_oriented_scores": {
                "fundamental_problems": 6,
                "academic_publications": 5,
                "research_background": 6,
                "technical_roadmap": 7,
                "academic_collaboration": 4,
                "emerging_tech": 6,
                "scientific_goals": 5
            },
            "intelligence_oriented_scores": {
                "intelligent_processing": 8,
                "specialized_expertise": 7,
                "new_insights": 8,
                "intellectual_barrier": 7,
                "learning_improvement": 7
            },
            "resource_oriented_scores": {
                "computational_value": 6,
                "hardware_requirements": 7,
                "resource_provider": 6,
                "geographic_importance": 5,
                "redundancy_value": 6,
                "resource_returns": 7
            },
            "additional_criteria_scores": {
                "scores": {
                    "substrate_registration": 2,
                    "current_revenue": 5,
                    "revenue_prospects": 3,
                    "team_quantifiable": 4,
                    "team_track_record": 4,
                    "competitive_viability": 3,
                    "total_addressable_market": 3,
                    "roadmap_quality": 1,
                    "documentation_quality": 3,
                    "ui_ux_quality": 2,
                    "github_activity": 1,
                    "twitter_activity": 1,
                    "dtao_marketing": 5,
                    "third_party_integrations": 1,
                    "partnerships": 0,
                    "subnet_uniqueness": 5,
                    "interoperability": 0,
                    "miner_rewards": 0,
                    "subnet_integration": 6
                },
                "weights": weights_data
            }
        },
        {
            "name": "τargon",
            "uid": "4",
            "description": "Advanced subnet with a custom evaluation score of 3.0.",
            "service_oriented_scores": {
                "functioning_product": 8,
                "immediate_utility": 7,
                "revenue_model": 8,
                "apis_integrations": 6,
                "validator_monetization": 7,
                "usage_metrics": 8,
                "implementation_docs": 7,
                "real_world_use_cases": 8
            },
            "research_oriented_scores": {
                "fundamental_problems": 7,
                "academic_publications": 6,
                "research_background": 7,
                "technical_roadmap": 8,
                "academic_collaboration": 5,
                "emerging_tech": 7,
                "scientific_goals": 6
            },
            "intelligence_oriented_scores": {
                "intelligent_processing": 9,
                "specialized_expertise": 8,
                "new_insights": 7,
                "intellectual_barrier": 8,
                "learning_improvement": 7
            },
            "resource_oriented_scores": {
                "computational_value": 7,
                "hardware_requirements": 8,
                "resource_provider": 7,
                "geographic_importance": 6,
                "redundancy_value": 7,
                "resource_returns": 8
            },
            "additional_criteria_scores": {
                "scores": {
                    "substrate_registration": 6,
                    "current_revenue": 2,
                    "revenue_prospects": 4,
                    "team_quantifiable": 3,
                    "team_track_record": 2,
                    "competitive_viability": 3,
                    "total_addressable_market": 3,
                    "roadmap_quality": 1,
                    "documentation_quality": 1,
                    "ui_ux_quality": 3,
                    "github_activity": 1,
                    "twitter_activity": 1,
                    "dtao_marketing": 1,
                    "third_party_integrations": 2,
                    "partnerships": 0,
                    "subnet_uniqueness": 2,
                    "interoperability": 1,
                    "miner_rewards": 0,
                    "subnet_integration": 7
                },
                "weights": weights_data
            }
        },
        {
            "name": "ץ neural",
            "uid": "46",
            "description": "Innovative neural network subnet with a custom evaluation score of 1.8.",
            "service_oriented_scores": {
                "functioning_product": 7,
                "immediate_utility": 6,
                "revenue_model": 7,
                "apis_integrations": 8,
                "validator_monetization": 6,
                "usage_metrics": 7,
                "implementation_docs": 6,
                "real_world_use_cases": 7
            },
            "research_oriented_scores": {
                "fundamental_problems": 6,
                "academic_publications": 5,
                "research_background": 6,
                "technical_roadmap": 7,
                "academic_collaboration": 4,
                "emerging_tech": 6,
                "scientific_goals": 5
            },
            "intelligence_oriented_scores": {
                "intelligent_processing": 8,
                "specialized_expertise": 7,
                "new_insights": 8,
                "intellectual_barrier": 7,
                "learning_improvement": 8
            },
            "resource_oriented_scores": {
                "computational_value": 5,
                "hardware_requirements": 6,
                "resource_provider": 5,
                "geographic_importance": 4,
                "redundancy_value": 5,
                "resource_returns": 6
            },
            "additional_criteria_scores": {
                "scores": {
                    "substrate_registration": 5,
                    "current_revenue": 1,
                    "revenue_prospects": 3,
                    "team_quantifiable": 4,
                    "team_track_record": 3,
                    "competitive_viability": 3,
                    "total_addressable_market": 3,
                    "roadmap_quality": 1,
                    "documentation_quality": 2,
                    "ui_ux_quality": 2,
                    "github_activity": 1,
                    "twitter_activity": 1,
                    "dtao_marketing": 2,
                    "third_party_integrations": 1,
                    "partnerships": 0.5,
                    "subnet_uniqueness": 2,
                    "interoperability": 1,
                    "miner_rewards": 0,
                    "subnet_integration": 8
                },
                "weights": weights_data
            }
        },
        {
            "name": "ب frontier",
            "uid": "53",
            "description": "Frontier-focused subnet with a custom evaluation score of 2.0.",
            "service_oriented_scores": {
                "functioning_product": 6,
                "immediate_utility": 7,
                "revenue_model": 6,
                "apis_integrations": 7,
                "validator_monetization": 6,
                "usage_metrics": 7,
                "implementation_docs": 6,
                "real_world_use_cases": 7
            },
            "research_oriented_scores": {
                "fundamental_problems": 5,
                "academic_publications": 6,
                "research_background": 5,
                "technical_roadmap": 6,
                "academic_collaboration": 5,
                "emerging_tech": 6,
                "scientific_goals": 5
            },
            "intelligence_oriented_scores": {
                "intelligent_processing": 7,
                "specialized_expertise": 6,
                "new_insights": 7,
                "intellectual_barrier": 6,
                "learning_improvement": 7
            },
            "resource_oriented_scores": {
                "computational_value": 6,
                "hardware_requirements": 5,
                "resource_provider": 6,
                "geographic_importance": 5,
                "redundancy_value": 6,
                "resource_returns": 5
            },
            "additional_criteria_scores": {
                "scores": {
                    "substrate_registration": 4,
                    "current_revenue": 0.5,
                    "revenue_prospects": 1,
                    "team_quantifiable": 4,
                    "team_track_record": 3,
                    "competitive_viability": 2,
                    "total_addressable_market": 3,
                    "roadmap_quality": 1,
                    "documentation_quality": 0.15,
                    "ui_ux_quality": 0,
                    "github_activity": 0,
                    "twitter_activity": 0.2,
                    "dtao_marketing": 0.05,
                    "third_party_integrations": 0.3,
                    "partnerships": 0.1,
                    "subnet_uniqueness": 0,
                    "interoperability": 0,
                    "miner_rewards": 0,
                    "subnet_integration": 9
                },
                "weights": weights_data
            }
        }
    ]
    
    # Save each subnet
    for subnet_data in example_subnets:
        save_subnet(subnet_data)

# Main app function
def main():
    """Main application entry point."""
    try:
        # Initialize database
        init_db()
        
        # Set up page config
        set_page_config()
        
        # Add logging info
        print("LOG: Starting Sherpa - Bittensor Subnet Evaluation Tool")
        
        # Run navigation
        navigation()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        print(f"ERROR: {str(e)}")
        # Add a fallback basic UI in case of error
        st.markdown("## Sherpa - Bittensor Subnet Evaluation Tool")
        st.markdown("There was an error loading the application. Please try refreshing the page.")

if __name__ == "__main__":
    main()