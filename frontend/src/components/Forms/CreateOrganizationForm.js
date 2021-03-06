import react, { useState, useContext } from "react";
import { Form, Row } from "react-bootstrap";
import AuthContext from "../store/auth-context";
import { axiosInstance, url } from "../store/api";
import "../Modals/Modal.css";

const CreateOrganizationForm = (props) => {
  const authCtx = useContext(AuthContext);
  const [name, setName] = useState("");
  console.log(props);

  const submitHandler = (e) => {
    console.log("submit handler ran");
    e.preventDefault();
    axiosInstance
      .post(
        `${url}/create-organization/`,
        { name: name },
        { headers: { Authorization: "Bearer " + authCtx.access } }
      )
      .then((res) => {
        if (res.status == 200) {
        }
        let newOrganizationId = res.data.id;
        axiosInstance
          .get(`/boards`, {
            headers: { Authorization: "Bearer " + authCtx.access },
          })
          .then((response) => {
            if (response.status === 200) {
              console.log(response.data);
              let newOrganizations = response.data.organizations;
              props.setData({ ...props.data, organizations: newOrganizations });
            } else {
              console.log("error"); //! handle this error properly
            }
          });
        props.closeCreateOrganizationModal();
      });
  };

  return (
    <Form onSubmit={submitHandler} id="CreateOrganizationForm">
      <div className="form-content">
        <Form.Group controlId="formName" className="mt-2">
          <h6>Organization Name</h6>
          <Form.Control
            as="textarea"
            onChange={(e) => {
              setName(e.target.value);
            }}
          />
        </Form.Group>
      </div>
    </Form>
  );
};

export default CreateOrganizationForm;
