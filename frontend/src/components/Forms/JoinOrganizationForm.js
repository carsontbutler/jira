import react, { useState, useContext } from "react";
import { Form, Row } from "react-bootstrap";
import AuthContext from "../store/auth-context";
import { axiosInstance, url } from "../store/api";
import "../Modals/Modal.css";

const JoinOrganizationForm = (props) => {
  const authCtx = useContext(AuthContext);
  const [code, setCode] = useState("");
  console.log(props);

  const submitHandler = (e) => {
    console.log("submit handler ran");
    e.preventDefault();
    axiosInstance
      .post(
        `${url}/join-organization/`,
        { code: code },
        { headers: { Authorization: "Bearer " + authCtx.access } }
      )
      .then((res) => {
        if (res.status == 200) {
        }
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
        props.closeJoinOrganizationModal();
      });
  };

  return (
    <Form onSubmit={submitHandler} id="JoinOrganizationForm">
      <div className="form-content">
        <Form.Group controlId="formName" className="mt-2">
          <h6>Organization Code</h6>
          <Form.Control
            as="textarea"
            onChange={(e) => {
              setCode(e.target.value);
            }}
          />
        </Form.Group>
      </div>
    </Form>
  );
};

export default JoinOrganizationForm;