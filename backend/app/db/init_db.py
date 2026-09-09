import asyncio
import json
from pathlib import Path
from decimal import Decimal

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine, SessionLocal, Base
from app.models.location import Country, State, City
from app.models.food import Food, FoodAllergen, FoodPrice, FoodRegion
from app.models.recipe import Recipe, RecipeIngredient, RecipeDietCompatibility, RecipeMealType, RecipeCuisine, RecipeRegion, RecipeAllergen
from app.models.medical import MedicalRule, MedicalRuleConstraint

DATA_DIR = Path(__file__).parent.parent / "data"

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with SessionLocal() as session:
        await load_locations(session)
        await load_foods(session)
        await load_recipes(session)
        await load_medical_rules(session)
        await session.commit()
        print("Database seeded successfully.")

async def load_locations(session: AsyncSession):
    print("Loading locations...")
    file_path = DATA_DIR / "seed_locations.json"
    if not file_path.exists():
        return
        
    with open(file_path, "r") as f:
        data = json.load(f)
        
    for c_data in data.get("countries", []):
        stmt = select(Country).where(Country.code == c_data["code"])
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            session.add(Country(**c_data))
            
    for s_data in data.get("states", []):
        stmt = select(State).where(and_(State.country_code == s_data["country_code"], State.code == s_data["code"]))
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            session.add(State(**s_data))

    for c_data in data.get("cities", []):
        stmt = select(City).where(and_(City.country_code == c_data["country_code"], City.state_code == c_data["state_code"], City.name == c_data["name"]))
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            session.add(City(**c_data))
            
    await session.commit()

async def load_foods(session: AsyncSession):
    print("Loading foods...")
    foods_file = DATA_DIR / "seed_foods.json"
    prices_file = DATA_DIR / "seed_food_prices.json"
    regions_file = DATA_DIR / "seed_food_regions.json"
    
    with open(foods_file, "r") as f:
        foods_data = json.load(f)
        
    food_id_map = {}
    for f_data in foods_data:
        stmt = select(Food).where(Food.name == f_data["name"])
        res = await session.execute(stmt)
        food = res.scalar_one_or_none()
        if not food:
            food = Food(
                name=f_data["name"],
                category=f_data["category"],
                calories_per_100g=Decimal(str(f_data["calories_per_100g"])),
                protein_per_100g=Decimal(str(f_data["protein_per_100g"])),
                carbs_per_100g=Decimal(str(f_data["carbs_per_100g"])),
                fat_per_100g=Decimal(str(f_data["fat_per_100g"])),
                fiber_per_100g=Decimal(str(f_data["fiber_per_100g"])),
                sodium_per_100g=Decimal(str(f_data["sodium_per_100g"])),
                serving_size_g=Decimal(str(f_data["serving_size_g"])),
                is_vegan=f_data["is_vegan"],
                is_vegetarian=f_data["is_vegetarian"],
                seasonality=f_data["seasonality"],
                nutrition_source=f_data["nutrition_source"],
                nutrition_source_id=f_data["nutrition_source_id"]
            )
            session.add(food)
            await session.flush()
        food_id_map[food.name] = food.id

    if prices_file.exists():
        with open(prices_file, "r") as f:
            prices_data = json.load(f)
        for p_data in prices_data:
            food_id = food_id_map.get(p_data["food_name"])
            if not food_id: continue
            
            stmt = select(FoodPrice).where(and_(FoodPrice.food_id == food_id, FoodPrice.state_code == p_data["state_code"]))
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                price = FoodPrice(
                    food_id=food_id,
                    country_code=p_data["country_code"],
                    state_code=p_data["state_code"],
                    city=p_data["city"],
                    price_per_unit=Decimal(str(p_data["price_per_unit"])),
                    currency=p_data["currency"],
                    unit=p_data["unit"],
                    typical_package_size_g=Decimal(str(p_data["typical_package_size_g"])),
                    typical_package_price=Decimal(str(p_data["typical_package_price"])),
                    source=p_data["source"],
                    source_url=p_data["source_url"]
                )
                session.add(price)

    if regions_file.exists():
        with open(regions_file, "r") as f:
            regions_data = json.load(f)
        for r_data in regions_data:
            food_id = food_id_map.get(r_data["food_name"])
            if not food_id: continue
            
            stmt = select(FoodRegion).where(and_(FoodRegion.food_id == food_id, FoodRegion.state_code == r_data["state_code"]))
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                region = FoodRegion(
                    food_id=food_id,
                    country_code=r_data["country_code"],
                    state_code=r_data["state_code"],
                    availability_score=Decimal(str(r_data["availability_score"]))
                )
                session.add(region)

    await session.commit()

async def load_recipes(session: AsyncSession):
    print("Loading recipes...")
    recipes_file = DATA_DIR / "seed_recipes.json"
    regions_file = DATA_DIR / "seed_recipe_regions.json"
    
    with open(recipes_file, "r") as f:
        recipes_data = json.load(f)
        
    stmt = select(Food)
    res = await session.execute(stmt)
    foods_lookup = {f.name: f for f in res.scalars().all()}
    
    recipe_id_map = {}
    
    for r_data in recipes_data:
        stmt = select(Recipe).where(Recipe.name == r_data["name"])
        res = await session.execute(stmt)
        recipe = res.scalar_one_or_none()
        
        if not recipe:
            total_cal = total_prot = total_carb = total_fat = total_fiber = total_sodium = Decimal(0)
            
            for ing in r_data["ingredients"]:
                food = foods_lookup.get(ing["food_name"])
                if not food:
                    print(f"Warning: Food {ing['food_name']} not found for recipe {r_data['name']}")
                    continue
                factor = Decimal(str(ing["quantity_g"])) / Decimal("100.0")
                total_cal += food.calories_per_100g * factor
                total_prot += food.protein_per_100g * factor
                total_carb += food.carbs_per_100g * factor
                total_fat += food.fat_per_100g * factor
                total_fiber += food.fiber_per_100g * factor
                total_sodium += food.sodium_per_100g * factor
                
            recipe = Recipe(
                name=r_data["name"],
                description=r_data["description"],
                prep_time_min=r_data["prep_time_min"],
                difficulty=r_data["difficulty"],
                estimated_cost=Decimal(str(r_data["estimated_cost"])),
                cost_currency=r_data["cost_currency"],
                servings=r_data["servings"],
                instructions=r_data["instructions"],
                calories=total_cal,
                protein_g=total_prot,
                carbs_g=total_carb,
                fat_g=total_fat,
                fiber_g=total_fiber,
                sodium_mg=total_sodium
            )
            session.add(recipe)
            await session.flush()
            
            for ing in r_data["ingredients"]:
                food = foods_lookup.get(ing["food_name"])
                if food:
                    session.add(RecipeIngredient(
                        recipe_id=recipe.id,
                        food_id=food.id,
                        quantity_g=Decimal(str(ing["quantity_g"])),
                        unit=ing["unit"],
                        is_optional=ing.get("is_optional", False)
                    ))
                    
            for dt in r_data["diet_compatibility"]:
                session.add(RecipeDietCompatibility(recipe_id=recipe.id, diet_type=dt))
                
            for mt in r_data["meal_types"]:
                session.add(RecipeMealType(recipe_id=recipe.id, meal_type=mt))
                
            for c in r_data["cuisines"]:
                session.add(RecipeCuisine(recipe_id=recipe.id, cuisine=c))
                
            for al in r_data.get("allergens", []):
                session.add(RecipeAllergen(recipe_id=recipe.id, allergen=al))
                
        recipe_id_map[recipe.name] = recipe.id
        
    if regions_file.exists():
        with open(regions_file, "r") as f:
            regions_data = json.load(f)
            
        for r_data in regions_data:
            recipe_id = recipe_id_map.get(r_data["recipe_name"])
            if not recipe_id: continue
            
            stmt = select(RecipeRegion).where(and_(RecipeRegion.recipe_id == recipe_id, RecipeRegion.state_code == r_data["state_code"]))
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                session.add(RecipeRegion(
                    recipe_id=recipe_id,
                    country_code=r_data["country_code"],
                    state_code=r_data["state_code"],
                    relevance_score=Decimal(str(r_data["relevance_score"]))
                ))
                
    await session.commit()

async def load_medical_rules(session: AsyncSession):
    print("Loading medical rules...")
    file_path = DATA_DIR / "seed_medical_rules.json"
    if not file_path.exists():
        return
        
    with open(file_path, "r") as f:
        rules_data = json.load(f)
        
    for r_data in rules_data:
        stmt = select(MedicalRule).where(MedicalRule.condition == r_data["condition"])
        res = await session.execute(stmt)
        rule = res.scalar_one_or_none()
        
        if not rule:
            rule = MedicalRule(
                condition=r_data["condition"],
                description=r_data["description"],
                source=r_data["source"],
                source_url=r_data.get("source_url"),
                version=r_data["version"],
                reviewed_by=r_data["reviewed_by"],
                is_validated=r_data["is_validated"]
            )
            session.add(rule)
            await session.flush()
            
            for c_data in r_data.get("rules", []):
                session.add(MedicalRuleConstraint(
                    rule_id=rule.id,
                    nutrient=c_data["nutrient"],
                    operator=c_data["operator"],
                    value=Decimal(str(c_data["value"])),
                    scope=c_data["scope"],
                    unit=c_data["unit"]
                ))
                
    await session.commit()

if __name__ == "__main__":
    asyncio.run(init_db())
