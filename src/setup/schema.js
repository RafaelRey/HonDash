/* units */
var temp_units = ["celsius", "fahrenheit"];
var speed_units = ["kmh", "mph"];
var mixture_units = ["afr", "lambda"];
var pressure_units = ["psi", "bar"];
var per_cent_units = ["per cent"];
var distance_units = ["km", "miles"];

/* util functions */
function unit(units){
    return {"type": "string", "enum": units};
}
function simple_value_no_units(sectors) {
    var config = simple_value(sectors);
    delete config["required"].splice(1);
    delete config["properties"]["unit"];
    return config;
}
function simple_value_no_units_no_decimals(sectors) {
    var config = simple_value_no_units(sectors);
    delete config["properties"]["decimals"];
    return config;
}
function simple_value_no_decimals(sectors, units) {
    var config = simple_value(units, sectors);
    delete config["properties"]["decimals"];
    return config;
}
function simple_value(sectors, units) {
   return {
       "type": "object",
       "required": ["tag", "unit"],
       "properties": {
           "tag": tag,
           "unit": unit(units),
           "decimals": decimals,
           "label": label,
           "suffix": suffix,
           "max": max,
           "sectors": sectors
        }
    };
}

/* fields */
var tag = {
    "type": "string",
    "enum": ["not use","gauge1", "gauge2", "gauge3", "gauge4", "gauge5", "gauge6", "gauge7", "gauge8", "gauge9", "gauge10", "time", "odo", "bar1", "bar2", "icon1", "icon2", "gear", "speed"]
};
var formula = {
    "type": "string",
    "enum": ["autometer_2246", "vdo_323_057", "aem_30_2012", "ebay_150_psi", "bosch_0280130039_0280130026", "civic_eg_fuel_tank", "s2000_fuel_tank", "mr2_w30_fuel_tank", "mx5_na_fuel_tank"]
};
var time = {
    "type": "object",
    "required": ["tag"],
    "properties": {
        "tag": tag
    }
};
var screen = {
    "type": "object",
    "required": ["rotate"],
    "properties": {
        "rotate": {"type": "boolean"}
    }
};
var sectors = {
    "type": "array",
    "format": "table",
    "items": {
        "type":"object",
        "properties": {
            "lo": {
                "type": "integer"
            },
            "hi": {
                "type": "integer"
            },
            "color": {
                "type": "string",
                "format": "color"
            }
        }
    }
};

var sectors_decimals = {
    "type": "array",
    "format": "table",
    "items": {
        "type":"object",
        "properties": {
            "lo": {
                "type": "number"
            },
            "hi": {
                "type": "number"
            },
            "color": {
                "type": "string",
                "format": "color"
            }
        }
    }
};

var odo = {
    "type": "object",
    "required": ["tag", "unit"],
    "properties": {
        "tag": tag,
        "unit": unit(distance_units),
        "suffix": suffix,
        "value": {"type": "number"}
    }
};
var rpm = {
    "type": "object",
    "required": ["tag"],
    "properties": {
        "tag": tag,
        "suffix": suffix,
        "max": {"type": "integer"},
        "sectors": sectors
    }
};
var mil = {
    "type": "object",
    "required": ["tag"],
    "properties": {
        "tag": tag,
        "pathon": {"type": "string"},
        "pathoff": {"type": "string"}
    }
};
var fan = {
    "type": "object",
    "required": ["tag"],
    "properties": {
        "tag": tag,
        "pathon": {"type": "string"},
        "pathoff": {"type": "string"}
    }
};
var gear = {
    "type": "object",
    "required": ["tag"],
    "properties": {
        "tag": tag
    }
};
var template = {
    "type": "string",
    "required": true,
    "enum": ["basic", "animalillo"],
    "links": [
        {"mediaType": "image",
        "href": "templates/{{self}}.png"}
        ]
};
var map = {
    "type": "object",
    "required": ["tag", "unit"],
    "properties": {
        "tag": tag,
        "unit": unit(pressure_units),
        "decimals": decimals,
        "label": label,
        "suffix": suffix,
        "max": max,
        "sectors": sectors_decimals
    }
};
var label = {"type": "string"};
var max = {"type": "integer"};
var decimals = {"type": "integer"};
var suffix = {"type": "string"};
var analog = {
    "type": "object",
    "required": ["tag", "unit", "formula"],
    "properties": {
        "tag": tag,
        "unit": unit(temp_units.concat(pressure_units).concat(per_cent_units)),
        "decimals": decimals,
        "formula": formula,
        "label": label,
        "suffix": suffix,
        "max": max,
        "sectors": sectors_decimals
    }
};

var schema = {
    schema: {
        "type": "object",
        "title": "HonDash setup",
        "hideTitle": true,
        "properties": {
            "template": template,
            "screen": screen,
            "time": time,
            "odo": odo,
            "gear": gear,
            "rpm": rpm,
            "mil": mil,
            "fan": fan,
            "eth": simple_value_no_units_no_decimals(sectors),
            "vss": simple_value_no_decimals(speed_units, sectors),
            "cam": simple_value_no_units_no_decimals(sectors),
            "bat": simple_value_no_units(sectors_decimals),
            "tps": simple_value_no_units_no_decimals(sectors),
            "iat": simple_value_no_decimals(temp_units, sectors),
            "ect": simple_value_no_decimals(temp_units, sectors),
            "o2": simple_value(sectors_decimals, mixture_units),
            "map": map,
            "an0": analog,
            "an1": analog,
            "an2": analog,
            "an3": analog,
            "an4": analog,
            "an5": analog,
            "an6": analog,
            "an7": analog
        }
    },
    no_additional_properties: true,
    disable_collapse: true,
    disable_edit_json: true,
    disable_properties: true,
    disable_array_delete_last_row: true,
    disable_array_reorder: true,
    theme: 'bootstrap3'
};