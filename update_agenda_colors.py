from app import app, db
from models import User
import sys

def update_colors():
    with app.app_context():
        # Map of partial name to color
        # Leopoldo: Blue (#0000FF)
        # Mateus: Green (#008000)
        # Isadora: Yellow (#FFFF00)
        # Luciana: Orange (#FFA500)
        # admin: Black (#000000)
        
        color_map = {
            'leopoldo': '#0000FF',
            'mateus': '#008000',
            'isadora': '#FFFF00', # Using standard Yellow as requested
            'luciana': '#FFA500', 
            'admin': '#000000'
        }
        
        print("Starting Agenda Color Update...")
        
        users = User.query.all()
        updated_count = 0
        
        for user in users:
            name_lower = (user.nome_completo or user.username).lower()
            
            # Check for matches
            matched = False
            for key, color in color_map.items():
                if key in name_lower or (user.username and key in user.username.lower()):
                    old_color = user.cor_agenda
                    user.cor_agenda = color
                    print(f"✅ Updating {user.username} ({user.nome_completo}): {old_color} -> {color}")
                    matched = True
                    updated_count += 1
                    break
            
            if not matched:
                # Optional: log unmatched users
                # print(f"ℹ️  Skipping {user.username} ({user.nome_completo}) - No match found")
                pass

        if updated_count > 0:
            db.session.commit()
            print(f"\n🎉 Successfully updated {updated_count} users' agenda colors.")
        else:
            print("\n⚠️ No users matched the criteria.")

if __name__ == "__main__":
    try:
        update_colors()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
