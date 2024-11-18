

class Hook {
    /**
     * Form hook
     * @constructor
     * @param {Object} globalConfig - Global configuration.
     * @param {string} serviceName - Service name
     * @param {object} state - object with state of the components on the servcice/page
     * @param {string} mode - edit,create or clone
     * @param {object} util - the utility object
     */
    constructor(globalConfig, serviceName, state, mode, util, groupName) {
        this.globalConfig = globalConfig;
        this.serviceName = serviceName;
        this.state = state;
        this.mode = mode;
        this.util = util;
        this.groupName = groupName;
        this._debouncedNameChange = this.debounce(this._nameChange.bind(this), 200);
    }

    onCreate() {

        if (this.mode == "create") {
            this.util.setState((prevState) => {
                let data = { ...prevState.data };
                data.collect_collaboration.display = false
                data.event_delay.display = false
                data.collect_folder.display = false
                data.collect_file.display = false
                data.collect_task.display = false
                data.created_after.display = false
                return { data };
            });
        }
        
    }

    debounce(func, wait) {

        let timeout;
        return function executedFunction(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => {func(...args)}, wait);
        }
    }

    onChange(field, value, dataDict) {

        if(value == "events"){

            this.util.setState((prevState) => {

                let data = { ...prevState.data };

                data.event_delay.display = true
                data.created_after.display = true
                data.collect_collaboration.display = false
                data.collect_folder.display = false
                data.collect_file.display = false
                data.collect_task.display = false
                data.duration.value = 120
                data.interval.value = 120
               
                return { data };
            })
        }

        else if(value == "users" || value == "groups"){

            this.util.setState((prevState) => {

                let data = { ...prevState.data };
                
                data.collect_collaboration.display = false
                data.event_delay.display = false
                data.collect_folder.display = false
                data.collect_file.display = false
                data.collect_task.display = false
                data.created_after.display = false
                data.duration.value = 604800
                data.interval.value = 604800
                

                return { data };
            })

        }
        else if(value == "folders"){

            this.util.setState((prevState) => {

                let data = { ...prevState.data };
                data.collect_collaboration.display = true
                data.collect_folder.display = true
                data.collect_file.display = true
                data.collect_task.display = true
                data.created_after.display = false
                data.event_delay.display = false
                data.duration.value = 604800 
                data.interval.value = 604800   

                return { data };
            })

        }
    }


    onRender() {

        if (this.mode == "clone"){

            this.util.setState((prevState) => {

                let data = { ...prevState.data };

                if(data.rest_endpoint.value == "events"){

                    data.event_delay.display = true
                    data.created_after.display = true
                    data.collect_collaboration.display = false
                    data.collect_folder.display = false
                    data.collect_file.display = false
                    data.collect_task.display = false

                }
        
                else if(data.rest_endpoint.value == "users" || data.rest_endpoint.value == "groups"){

                    data.collect_collaboration.display = false
                    data.event_delay.display = false
                    data.collect_folder.display = false
                    data.collect_file.display = false
                    data.collect_task.display = false
                    data.created_after.display = false

                }
                else if(data.rest_endpoint.value == "folders"){
        
                    data.collect_collaboration.display = true
                    data.collect_folder.display = true
                    data.collect_file.display = true
                    data.collect_task.display = true
                    data.created_after.display = false
                    data.event_delay.display = false       
                }
                
                return { data };
            });
        }
    }

    onSave(dataDict) {

        var accountname = dataDict.name;
        var auth_type = "oauth";

        this.util.setState((prevState) => {
            let new_state = this.util.clearAllErrorMsg(prevState);
            return new_state
        });

       
        if (accountname === null || accountname.trim().length === 0) {
            var msg = "Field account name is required";
            this.util.setErrorMsg(msg);
            return false;
        } 
    
        else if (auth_type == "oauth") {
          
            this.util.setState((prevState) => {
                
                let data = { ...prevState.data };
                let endpoint = data.rest_endpoint.value

                // required to set input_name
                data.input_name.value = data.name.value;

                if (endpoint === "groups" || endpoint === "users" || endpoint === "events" ){
                    
                    data.collect_task.value = 0
                    data.collect_file.value = 0
                    data.collect_folder.value = 0
                    data.collect_collaboration.value = 0
                }
                    return { data };
                });
        }

        return true;
    }

    onSaveSuccess() {

    }

    onSaveFail() {

    }

    onEditLoad() {
        
        if (this.mode == "edit") {
            
            this.util.setState((prevState) => {

                let data = { ...prevState.data };

                if(data.rest_endpoint.value == "events"){

                    data.event_delay.display = true
                    data.created_after.display = true
                    data.collect_collaboration.display = false
                    data.collect_folder.display = false
                    data.collect_file.display = false
                    data.collect_task.display = false

                }
        
                else if(data.rest_endpoint.value == "users" || data.rest_endpoint.value == "groups"){

                    data.collect_collaboration.display = false
                    data.event_delay.display = false
                    data.collect_folder.display = false
                    data.collect_file.display = false
                    data.collect_task.display = false
                    data.created_after.display = false

                }
                else if(data.rest_endpoint.value == "folders"){
        
                    data.collect_collaboration.display = true
                    data.collect_folder.display = true
                    data.collect_file.display = true
                    data.collect_task.display = true
                    data.created_after.display = false
                    data.event_delay.display = false
                        
                }

                return { data };
            });
        }
    }

    _nameChange(dataDict) {
    }
}

export default Hook;
