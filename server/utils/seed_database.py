import csv
import os
import sys
import random
from datetime import datetime, timedelta
from collections import defaultdict

# Add the parent directory to sys.path to allow importing from models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import init_db, db, Breed, Dog
from models.dog import AdoptionStatus

def create_app():
    """Create and configure Flask app for database operations"""
    app = Flask(__name__)
    
    # Get the server directory path (one level up from utils)
    server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(server_dir, "dogshelter.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the database with the app
    init_db(app)
    
    return app

def create_breeds():
    """Seed the database with breeds from the CSV file"""
    app = create_app()
    
    # Path to the CSV file
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'models', 'breeds.csv')
    
    with app.app_context():
        # Check if breeds already exist
        existing_breeds = Breed.query.count()
        if existing_breeds > 0:
            print(f"Database already contains {existing_breeds} breeds. Skipping seed.")
            return
        
        # Read the CSV file and add breeds to the database
        with open(csv_path, 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                breed = Breed(name=row['Breed'], description=row['Description'])
                db.session.add(breed)
            
            # Commit the changes
            db.session.commit()
            
        # Verify the seeding
        breed_count = Breed.query.count()
        print(f"Successfully seeded {breed_count} breeds to the database.")

def create_dogs():
    """Seed the database with dogs from the CSV file, ensuring at least 3 dogs per breed"""
    app = create_app()
    
    # Path to the CSV file
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'models', 'dogs.csv')
    
    with app.app_context():
        # Check if dogs already exist
        existing_dogs = Dog.query.count()
        if existing_dogs > 0:
            print(f"Database already contains {existing_dogs} dogs. Skipping seed.")
            return
        
        # Get all breeds from the database
        breeds = Breed.query.all()
        if not breeds:
            print("No breeds found in database. Please seed breeds first.")
            return
        
        # Track how many dogs are assigned to each breed
        breed_counts = defaultdict(int)
        
        # Read the CSV file
        dogs_data = []
        with open(csv_path, 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                dogs_data.append(row)
        
        def find_breed_for_dog(dog_info, breeds):
            """Try to find a matching breed based on the dog's description"""
            description = dog_info['Description'].lower()
            
            # Check if any breed name is mentioned in the description
            for breed in breeds:
                breed_name = breed.name.lower()
                # Check for exact breed name or common variations
                if breed_name in description:
                    return breed
                
                # Check for common breed keywords
                breed_keywords = {
                    'labrador': ['labrador', 'lab'],
                    'retriever': ['retriever'],
                    'bulldog': ['bulldog'],
                    'poodle': ['poodle'],
                    'shepherd': ['shepherd'],
                    'husky': ['husky'],
                    'beagle': ['beagle'],
                    'corgi': ['corgi'],
                    'boxer': ['boxer'],
                    'chihuahua': ['chihuahua'],
                    'schnauzer': ['schnauzer'],
                    'terrier': ['terrier'],
                    'labradoodle': ['labradoodle']
                }
                
                for key, keywords in breed_keywords.items():
                    if key in breed_name.lower():
                        for keyword in keywords:
                            if keyword in description:
                                return breed
            
            return None

        def create_dog(dog_info, breed_id):
            """Helper function to create a dog with consistent attributes"""
            dog = Dog(
                name=dog_info['Name'],
                description=dog_info['Description'],
                breed_id=breed_id,
                age=int(dog_info['Age']),
                gender=dog_info['Gender'],
                status=random.choice(list(AdoptionStatus)),
                intake_date=datetime.now() - timedelta(days=random.randint(1, 365))
            )
            db.session.add(dog)
            breed_counts[breed_id] += 1
            return dog
        
        # First pass: try to assign dogs to breeds based on their descriptions
        remaining_dogs = []
        for dog_info in dogs_data:
            matched_breed = find_breed_for_dog(dog_info, breeds)
            if matched_breed:
                create_dog(dog_info, matched_breed.id)
                print(f"Matched {dog_info['Name']} to {matched_breed.name} breed")
            else:
                remaining_dogs.append(dog_info)
        
        # Second pass: ensure each breed has at least 3 dogs by randomly assigning remaining dogs
        for breed in breeds:
            while breed_counts[breed.id] < 3 and remaining_dogs:
                dog_info = remaining_dogs.pop(0)
                create_dog(dog_info, breed.id)
        
        # Third pass: assign any remaining dogs randomly
        for dog_info in remaining_dogs:
            breed = random.choice(breeds)
            create_dog(dog_info, breed.id)
        
        # Commit all the changes
        db.session.commit()
        
        # Verify the seeding
        dog_count = Dog.query.count()
        print(f"Successfully seeded {dog_count} dogs to the database.")
        
        # Print distribution of dogs across breeds
        for breed in breeds:
            count = breed_counts[breed.id]
            print(f"Breed '{breed.name}': {count} dogs")

def seed_database():
    """Run all seeding functions in the correct order"""
    create_breeds()
    create_dogs()

if __name__ == '__main__':
    seed_database()