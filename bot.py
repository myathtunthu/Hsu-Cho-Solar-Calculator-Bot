Import telebot
from telebot import types
import time

# ==================== YOUR BOT TOKEN ====================
BOT_TOKEN = "8484357288:AAGM2TafS8FjLxZQ2gT1PVJ1prNepq-zuqc"
# ========================================================

bot = telebot.TeleBot(BOT_TOKEN)

print("Bot is starting with the provided token...")

# Store user data temporarily
user_data = {}

# Available solar panel wattages
SOLAR_PANEL_WATTAGES = [100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750]

# Available battery voltages
BATTERY_VOLTAGES = [12, 12.8, 22.8, 24, 25.6, 36, 48, 51.2, 60, 72, 96, 102.4]

# Battery types
BATTERY_TYPES = ["LiFePO4", "Lead-Acid", "Gel"]

# Step 1: Calculate total daily energy consumption
def calculate_daily_consumption(total_w, hours):
    return total_w * hours

# Step 2: Calculate battery size based on battery type
def calculate_battery_size(daily_wh, battery_voltage, battery_type="lifepo4"):
    if battery_type.lower() == "lifepo4":
        # LiFePO4 batteries can typically use 80-90% of their capacity
        dod_factor = 0.8  # Depth of Discharge (80%)
        battery_ah = (daily_wh / battery_voltage) * (1 / dod_factor)
    elif battery_type.lower() == "gel":
        # Gel batteries can use about 60% of their capacity
        dod_factor = 0.6  # Depth of Discharge (60%)
        battery_ah = (daily_wh / battery_voltage) * (1 / dod_factor)
    else:
        # Traditional lead-acid batteries should only use 50% of capacity
        dod_factor = 0.5  # Depth of Discharge (50%)
        battery_ah = (daily_wh / battery_voltage) * (1 / dod_factor)
    
    return battery_ah, dod_factor

# Step 3: Calculate solar panel requirements
def calculate_solar_panels(daily_wh, panel_wattage, sun_hours=5, efficiency=0.85):
    # Solar panel capacity needed considering system losses
    # efficiency factor includes charge controller, wiring, and battery losses
    solar_w = (daily_wh / sun_hours) * (1 / efficiency)
    
    # Calculate number of panels needed
    num_panels = round(solar_w / panel_wattage)
    if num_panels < 1:
        num_panels = 1
    
    return solar_w, num_panels

# Step 4: Calculate inverter size
def calculate_inverter_size(total_w):
    # Add 30% safety margin
    inverter_w = total_w * 1.3
    return inverter_w

# Step 5: Calculate charge controller size
def calculate_charge_controller(solar_w, battery_voltage):
    # For MPPT controllers (recommended for higher voltage systems)
    controller_amps = (solar_w / battery_voltage) * 1.25  # 25% safety margin
    
    # Determine controller type based on system size and voltage
    if solar_w <= 1000 and battery_voltage <= 24:
        controller_type = "PWM"
    else:
        controller_type = "MPPT"
    
    return controller_type, controller_amps

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        welcome_text = """
☀️ **MTT Solar Calculator မှ ကြိုဆိုပါတယ်!**

ဆိုလာစနစ်တွက်ချက်မှုအတွက် အဆင့် ၅ ဆင့်ဖြင့် တွက်ချက်ပေးပါမယ်:

1. စုစုပေါင်းစွမ်းအင်သုံးစွဲမှု
2. ဘက်ထရီအရွယ်အစား
3. ဆိုလာပြားလိုအပ်ချက်
4. အင်ဗာတာအရွယ်အစား
5. Charger Controller

🔧 **အသုံးပြုနည်း:**
/calculate - တွက်ချက်ရန်
/help - အကူအညီ
        """
        bot.reply_to(message, welcome_text, parse_mode='Markdown')
    except Exception as e:
        print("Error in start:", e)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📖 **အဆင့် ၅ ဆင့်ဖြင့် ဆိုလာစနစ်တွက်ချက်နည်း**

1. **စွမ်းအင်သုံးစွဲမှုဆန်းစစ်ခြင်း** - စုစုပေါင်း ဝပ်အားနှင့် အသုံးပြုမည့်နာရီ

2. **ဘက်ထရီအရွယ်အစား** - သင့်လိုအပ်ချက်အတွက် ဘက်ထရီ capacity တွက်ချက်ခြင်း

3. **ဆိုလာပြားလိုအပ်ချက်** - ဘက်ထရီကိုပြန်ဖြည့်ဖို့ လိုအပ်တဲ့ ဆိုလာပြားပမာဏ

4. **အင်ဗာတာအရွယ်အစား** - သင့်ပစ္စည်းအားလုံးကို ဖိလှိမ့်နိုင်ဖို့ အင်ဗာတာပမာဏ

5. **Charger Controller** - ဆိုလာစနစ်ကိုကာကွယ်ဖို့ လိုအပ်တဲ့ controller

💡 **ဥပမာ:**
- စုစုပေါင်းဝပ်အား: 500W
- အသုံးပြုမည့်နာရီ: 6 နာရီ

🔋 **ဘက်ထရီဗို့အား အကြံပြုချက်များ:**
- 12V: သေးငယ်သောစနစ်များ (1000W အောက်)
- 24V: အလတ်စားစနစ်များ (1000W-3000W)
- 48V/51.2V: ကြီးမားသောစနစ်များ (3000W အထက်)

/calculate ကိုနှိပ်ပြီး စတင်တွက်ချက်ပါ။
        """
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['calculate'])
def start_calculation(message):
    try:
        user_data[message.chat.id] = {}
        
        # Create keyboard for wattage knowledge
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
        buttons = [
            types.KeyboardButton("သိပါသည်"),
            types.KeyboardButton("မသိပါ")
        ]
        markup.add(*buttons)
        
        msg = bot.reply_to(message, "🔌 **သင့်စုစုပေါင်းဝပ်အား (W) ကိုသိပါသလား?**\n\nအောက်က လေးထောင့်ခလုတ်မှနှိပ်၍ ရွေးချယ်ပါ", reply_markup=markup)
        bot.register_next_step_handler(msg, handle_wattage_knowledge)
    except Exception as e:
        print("Error in calculate:", e)
        bot.reply_to(message, "❌ အမှားတစ်ခုဖြစ်နေပါတယ်")

def handle_wattage_knowledge(message):
    try:
        chat_id = message.chat.id
        response = message.text
        
        if response == "သိပါသည်":
            msg = bot.reply_to(message, "🔌 **ကျေးဇူးပြု၍ စုစုပေါင်းဝပ်အား (W) ထည့်ပါ**\n\nဥပမာ: 500", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, ask_usage_hours)
        elif response == "မသိပါ":
            # Send wattage calculation guide
            wattage_guide = """
🔋 **အဆင့် 1- သင့်စွမ်းအင်သုံးစွဲမှုကို အကဲဖြတ်ခြင်း။**

ဆိုလာစနစ်ဒီဇိုင်းအတွက် ပထမဆုံးခြေလှမ်းမှာ သင်နေ့စဉ်အသုံးပြုနေသော စွမ်းအင်ပမာဏကို နားလည်ခြင်းဖြစ်သည်။ ၎င်းသည် သင်၏ ဆိုလာပြားနှင့် ဘက်ထရီ လိုအပ်ချက် နှစ်ခုလုံးကို ဆုံးဖြတ်ရန် ကူညီပေးပါမည်။

**သင်၏နေ့စဉ်စွမ်းအင်သုံးစွဲမှုကို တွက်ချက်နည်း-**

1. **သင့်စက်ပစ္စည်းများကို စာရင်းပြုစုပါ။** - မီးများ၊ ရေခဲသေတ္တာများ၊ လေအေးပေးစက်များ၊ ကွန်ပျူတာများနှင့် ဖုန်းနှင့် လက်ပ်တော့များကဲ့သို့ သေးငယ်သော စက်ပစ္စည်းများအပါအဝင် နေရောင်ခြည်စွမ်းအင်ဖြင့် ပါဝါသုံးရန် သင်စီစဉ်ထားသော စက်ပစ္စည်းအားလုံးကို စာရင်းပြုစုခြင်းဖြင့် စတင်ပါ။

2. **Wattage ကိုစစ်ဆေးပါ။** - စက်ပစ္စည်းတိုင်းတွင် ပုံမှန်အားဖြင့် အညွှန်းတစ်ခု သို့မဟုတ် ထုတ်ကုန်လက်စွဲတွင် ဖော်ပြထားသော wattage အဆင့်ရှိသည်။ မဟုတ်ပါက၊ အသုံးများသော စက်ပစ္စည်းများ၏ ပုံမှန် ပါဝါသုံးစွဲမှုကို အွန်လိုင်းတွင် ရှာတွေ့နိုင်ပါသည်။

3. **နေ့စဉ်အသုံးပြုမှုကို တွက်ချက်ပါ။** - စက်တစ်ခုစီ၏ ဝပ်အားကို တစ်နေ့လျှင် ၎င်းအသုံးပြုသည့် နာရီအရေအတွက်ဖြင့် မြှောက်ပါ။ 

**ဥပမာ:** 100 watt မီးသီးသည် 5 နာရီကြာအလုပ်လုပ်သည်-
100W × 5 နာရီ = တစ်နေ့လျှင် 500Wh

4. **သင်၏အသုံးပြုမှုကို အနှစ်ချုပ်ပါ။** - စက်ပစ္စည်းတိုင်းအတွက် ၎င်းကို သင်လုပ်ဆောင်ပြီးသည်နှင့် သင်၏ စုစုပေါင်းစွမ်းအင်သုံးစွဲမှုကို ရှာဖွေရန် စက်အားလုံးအတွက် နေ့စဉ် ဝပ်နာရီများကို ပေါင်းထည့်ပါ။

**လက်တွေ့ကမ္ဘာ ဥပမာ-**

သင့်အိမ်တွင် အောက်ပါပစ္စည်းများကို အသုံးပြုသည်ဟု ဆိုကြပါစို့။
- ရေခဲသေတ္တာ 1 လုံး (150W) တစ်နေ့လျှင် 8 နာရီ အလုပ်လုပ်ပါသည်။
- LED မီးသီး 10 လုံး (10W တစ်ခုစီ) သည် တစ်နေ့လျှင် 5 နာရီ လည်ပတ်သည်။
- လေအေးပေးစက် 1 လုံး (1,500W) တစ်နေ့လျှင် 4 နာရီ လည်ပတ်သည်။

**စုစုပေါင်းနေ့စဉ်အသုံးပြုမှု-**
- ရေခဲသေတ္တာ: 150W × 8 နာရီ = 1,200Wh
- LED မီးများ: 10 × 10W × 5 နာရီ = 500Wh
- လေအေးပေးစက် : 1,500W × 4 နာရီ = 6,000Wh

**စုစုပေါင်းနေ့စဉ်စွမ်းအင်သုံးစွဲမှု = 1,200Wh + 500Wh + 6,000Wh = 7,700Wh (7.7kWh)**

🔌 **ကျေးဇူးပြု၍ စုစုပေါင်းဝပ်အား (W) ထည့်ပါ**\n\nဥပမာ: 770
            """
            msg = bot.reply_to(message, wattage_guide, parse_mode='Markdown')
            bot.register_next_step_handler(msg, ask_usage_hours)
        else:
            bot.reply_to(message, "❌ ကျေးဇူးပြု၍ 'သိပါသည်' သို့မဟုတ် 'မသိပါ' ကိုရွေးချယ်ပါ")
            
    except Exception as e:
        print("Error in handle_wattage_knowledge:", e)
        bot.reply_to(message, "❌ အမှားတစ်ခုဖြစ်နေပါတယ်")

def ask_usage_hours(message):
    try:
        chat_id = message.chat.id
        total_w = int(message.text)
        
        if total_w <= 0:
            bot.reply_to(message, "❌ ဝပ်အားသည် 0 ထက်ကြီးရပါမယ်")
            return
            
        user_data[chat_id]['total_w'] = total_w
        msg = bot.reply_to(message, f"⏰ **တစ်ရက်ကိုဘယ်နှနာရီသုံးမှာလဲ?**\n\nဥပမာ: 6")
        bot.register_next_step_handler(msg, ask_battery_type)
    except ValueError:
        bot.reply_to(message, "❌ ကျေးဇူးပြု၍ ဂဏန်းမှန်မှန်ထည့်ပါ\n\nဥပမာ: 500")
    except Exception as e:
        print("Error in ask_usage_hours:", e)
        bot.reply_to(message, "❌ အမှားတစ်ခုဖြစ်နေပါတယ်")

def ask_battery_type(message):
    try:
        chat_id = message.chat.id
        hours = float(message.text)
        
        if hours <= 0 or hours > 24:
            bot.reply_to(message, "❌ သုံးမည့်နာရီသည် 1 မှ 24 ကြားရှိရပါမယ်")
            return
            
        user_data[chat_id]['hours'] = hours
        
        # Create keyboard for battery type selection
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
        buttons = [types.KeyboardButton(b_type) for b_type in BATTERY_TYPES]
        markup.add(*buttons)
        
        msg = bot.reply_to(message, "🔋 **ဘက်ထရီအမျိုးအစားရွေးချယ်ပါ**\n\nအောက်က လေးထောင့်ခလုတ်မှနှိပ်၍ ရွေးချယ်ပါ", reply_markup=markup)
        bot.register_next_step_handler(msg, ask_solar_panel)
    except ValueError:
        bot.reply_to(message, "❌ ကျေးဇူးပြု၍ ဂဏန်းမှန်မှန်ထည့်ပါ\n\nဥပမာ: 6")
    except Exception as e:
        print("Error in ask_battery_type:", e)
        bot.reply_to(message, "❌ အမှားတစ်ခုဖြစ်နေပါတယ်")

def ask_solar_panel(message):
    try:
        chat_id = message.chat.id
        battery_type = message.text
        
        if battery_type not in BATTERY_TYPES:
            bot.reply_to(message, "❌ ကျေးဇူးပြု၍ ပေးထားသော option များထဲကေရေးချယ်ပါ")
            return
            
        user_data[chat_id]['battery_type'] = battery_type
        
        # Create keyboard for solar panel selection
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=3)
        buttons = [types.KeyboardButton(str(wattage)) for wattage in SOLAR_PANEL_WATTAGES]
        markup.add(*buttons)
        
        msg = bot.reply_to(message, "☀️ **ဆိုလာပြား Wattage ရွေးချယ်ပါ**\n\nအောက်က လေးထောင့်ခလုတ်မှနှိပ်၍ ရွေးချယ်ပါ", reply_markup=markup)
        bot.register_next_step_handler(msg, ask_battery_voltage)
    except Exception as e:
        print("Error in ask_solar_panel:", e)
        bot.reply_to(message, "❌ အမှားတစ်ခုဖြစ်နေပါတယ်")

def ask_battery_voltage(message):
    try:
        chat_id = message.chat.id
        panel_wattage = int(message.text)
        
        if panel_wattage not in SOLAR_PANEL_WATTAGES:
            bot.reply_to(message, "❌ ကျေးဇူးပြု၍ ပေးထားသော option များထဲကေရေးချယ်ပါ")
            return
            
        user_data[chat_id]['panel_wattage'] = panel_wattage
        
        # Create keyboard for battery voltage selection
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=3)
        buttons = [types.KeyboardButton(str(voltage)) for voltage in BATTERY_VOLTAGES]
        markup.add(*buttons)
        
        msg = bot.reply_to(message, "⚡ **ဘက်ထရီဗို့အားရွေးချယ်ပါ**\n\nအောက်က လေးထောင့်ခလုတ်မှနှိပ်၍ ရွေးချယ်ပါ", reply_markup=markup)
        bot.register_next_step_handler(msg, process_calculation)
    except ValueError:
        bot.reply_to(message, "❌ ကျေးဇူးပြု၍ ဂဏန်းမှန်မှန်ထည့်ပါ")
    except Exception as e:
        print("Error in ask_battery_voltage:", e)
        bot.reply_to(message, "❌ အမှားတစ်ခုဖြစ်နေပါတယ်")

def process_calculation(message):
    try:
        chat_id = message.chat.id
        battery_voltage = float(message.text)
        
        if battery_voltage not in BATTERY_VOLTAGES:
            bot.reply_to(message, "❌ ကျေးဇူးပြု၍ ပေးထားသော option များထဲကေရေးချယ်ပါ")
            return
        
        # Get user data
        total_w = user_data[chat_id]['total_w']
        hours = user_data[chat_id]['hours']
        panel_wattage = user_data[chat_id]['panel_wattage']
        battery_type = user_data[chat_id]['battery_type']
        
        # Perform all calculations
        # Step 1: Calculate daily consumption
        daily_wh = calculate_daily_consumption(total_w, hours)
        
        # Step 2: Calculate battery size
        battery_ah, dod_factor = calculate_battery_size(daily_wh, battery_voltage, battery_type.lower())
        
        # Step 3: Calculate solar panel requirements
        solar_w, num_panels = calculate_solar_panels(daily_wh, panel_wattage)
        
        # Step 4: Calculate inverter size
        inverter_w = calculate_inverter_size(total_w)
        
        # Step 5: Calculate charge controller
        controller_type, controller_amps = calculate_charge_controller(solar_w, battery_voltage)
        
        # Prepare result message
        result = f"""
📊 **MTT Solar Calculator - တွက်ချက်မှုရလဒ်များ**

🔋 **ဘက်ထရီအမျိုးအစား:** {battery_type}
⚡ **ဘက်ထရီဗို့အား:** {battery_voltage}V
☀️ **ဆိုလာပြား:** {panel_wattage}W
        
📝 **စွမ်းအင်သုံးစွဲမှုစာရင်း:**
• စုစုပေါင်းဝပ်အား: {total_w}W
• နေ့စဉ်သုံးစွဲမည့်နာရီ: {hours}h
• စုစုပေါင်းစွမ်းအင်သုံး စွဲမှု: {daily_wh:.0f} Wh/ရက်

🔋 **ဘက်ထရီအရွယ်အစား:** {battery_ah:.0f} Ah {battery_voltage}V
   - {battery_type} ဘက်ထရီ (DOD: {dod_factor*100:.0f}%)
   - {battery_ah:.0f}Ah ဘက်ထရီ ၁လုံး (သို့) သေးငယ်သောဘက်ထရီများကို parallel ချိတ်ဆက်အသုံးပြုနိုင်သည်

☀️ **ဆိုလာပြားလိုအပ်ချက်:** {solar_w:.0f} W
   - {panel_wattage}W ဆိုလာပြား {num_panels} ချပ်

⚡ **အင်ဗာတာအရွယ်အစား:** {inverter_w:.0f} W Pure Sine Wave
   - စုစုပေါင်းဝပ်အားထက် 30% ပိုကြီးသော အင်ဗာတာရွေးချယ်ထားသည်

🎛️ **ချားဂျီကွန်ထရိုလာ:** {controller_type} {controller_amps:.1f}A
   - {controller_type} ကွန်ထရိုလာ {controller_amps:.1f}A အရွယ်အစား

💡 **အထူးအကြံပြုချက်များ:"""
        
        if battery_type.lower() == "lifepo4":
            result += """
   - LiFePO4 ဘက်ထရီများသည် သက်တမ်းရှည်ပြီး စိတ်ချရမှုရှိသည်
   - 80% Depth of Discharge အထိ အသုံးပြုနိုင်သည်"""
        elif battery_type.lower() == "gel":
            result += """
   - Gel ဘက်ထရီများသည် ပြန်လည်အားသွင်းမှုမြန်ဆန်ပြီး ပြင်ပန်းသံဆူညံမှုနည်းသည်
   - 60% Depth of Discharge အထိ အသုံးပြုနိုင်သည်"""
        else:
            result += f"""
   - Lead-Acid ဘက်ထရီကို 50% ထက်ပို၍ မထုတ်သုံးသင့်ပါ
   - ရေမှန်မှန်ဖြည့်ပေးရန် လိုအပ်သည်"""
        
        # Add buttons to recalculate with different components
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("🔋 ဘက်ထရီအမျိုးအစားပြန်ရွေးမယ်", callback_data="change_battery_type"),
            types.InlineKeyboardButton("☀️ ဆိုလာပြားပြန်ရွေးမယ်", callback_data="change_solar")
        )
        markup.row(types.InlineKeyboardButton("🔄 အားလုံးပြန်ရွေးမယ်", callback_data="restart"))
        
        result += "\n\n🔁 **ထပ်တွက်ချင်ရင်** /calculate ကိုပြန်ရိုက်ပို့ပါ"
        
        bot.send_message(chat_id, result, parse_mode='Markdown', reply_markup=markup)
        
    except Exception as e:
        print("Error in process_calculation:", e)
        bot.reply_to(message, "❌ တွက်ချက်မှုမှားယွင်းနေပါတယ်")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        if call.data == "change_battery_type":
            # Create keyboard for battery type selection
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
            buttons = [types.KeyboardButton(b_type) for b_type in BATTERY_TYPES]
            markup.add(*buttons)
            
            bot.send_message(chat_id, "🔋 **ဘက်ထရီအမျိုးအစားအသစ်ရွေးချယ်ပါ**\n\nအောက်က လေးထောင့်ခလုတ်မှနှိပ်၍ ရွေးချယ်ပါ", reply_markup=markup)
            bot.register_next_step_handler_by_chat_id(chat_id, ask_solar_panel)
            
        elif call.data == "change_solar":
            # Create keyboard for solar panel selection
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=3)
            buttons = [types.KeyboardButton(str(wattage)) for wattage in SOLAR_PANEL_WATTAGES]
            markup.add(*buttons)
            
            bot.send_message(chat_id, "☀️ **ဆိုလာပြား Wattage အသစ်ရွေးချယ်ပါ**\n\nအောက်က လေးထောင့်ခလုတ်မှနှိပ်၍ ရွေးချယ်ပါ", reply_markup=markup)
            
            # We need to save the current state and ask for battery voltage again after solar selection
            def ask_battery_again(message):
                try:
                    panel_wattage = int(message.text)
                    if panel_wattage not in SOLAR_PANEL_WATTAGES:
                        bot.send_message(chat_id, "❌ ကျေးဇူးပြု၍ ပေးထားသော option များထဲကေရေးချယ်ပါ")
                        return
                    
                    user_data[chat_id]['panel_wattage'] = panel_wattage
                    
                    # Create keyboard for battery voltage selection
                    battery_markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=3)
                    battery_buttons = [types.KeyboardButton(str(voltage)) for voltage in BATTERY_VOLTAGES]
                    battery_markup.add(*battery_buttons)
                    
                    msg = bot.send_message(chat_id, "⚡ **ဘက်ထရီဗို့အားရွေးချယ်ပါ**\n\nအောက်က လေးထောင့်ခလုတ်မှနှိပ်၍ ရွေးချယ်ပါ", reply_markup=battery_markup)
                    bot.register_next_step_handler(msg, process_calculation)
                except ValueError:
                    bot.send_message(chat_id, "❌ ကျေးဇူးပြု၍ ဂဏန်း မှန်မှန်ထည့်ပါ")
            
            bot.register_next_step_handler_by_chat_id(chat_id, ask_battery_again)
            
        elif call.data == "restart":
            user_data[chat_id] = {}
            bot.send_message(chat_id, "🔄 **စနစ်အသစ်တွက်ချက်မည်**")
            msg = bot.send_message(chat_id, "🔌 **ကျေးဇူးပြု၍ စုစုပေါင်းဝပ်အား (W) ထည့်ပါ**\n\nဥပမာ: 500")
            bot.register_next_step_handler(msg, ask_usage_hours)
            
        # Delete the original message with buttons
        bot.delete_message(chat_id, message_id)
        
    except Exception as e:
        print("Error in callback handler:", e)
        bot.send_message(chat_id, "❌ အမှားတစ်ခုဖြစ်နေပါတယ်")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/'):
        bot.reply_to(message, "❌ မသိသော command ဖြစ်ပါတယ်\n\nအသုံးပြုရန်: /start or /calculate")
    else:
        bot.reply_to(message, "🤖 MTT Solar Calculator မှ ကြိုဆိုပါတယ်!\n\nစတင်ရန် /start ကိုရိုက်ပို့ပါ")

# Run the bot with error handling
try:
    print("Bot is running with token:", BOT_TOKEN)
    bot.polling(none_stop=True, interval=0, timeout=20)
except Exception as e:
    print("Bot polling error:", e)
    time.sleep(5)